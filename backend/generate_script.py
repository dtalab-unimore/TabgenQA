#!/usr/bin/env python3
"""
Worker script that runs Gradino generation in a subprocess.
Samples are generated one at a time and streamed as soon as they are ready, so that
progress is exact and already generated samples survive a stop.
Outputs JSON lines to stdout for the parent process to read:
  {"type": "status",   "message": ...}
  {"type": "progress", "current": i, "total": n, "progress": f, "desc": ...}
  {"type": "sample",   "data": {num_tables: {method: {perturbation: [records]}}}, "errors": [...]}  (one per sample)
  {"type": "done",     "errors": [...]}  (all errors, once at the end)
  {"type": "error",    "message": ..., "traceback": ...}
"""

import sys
import json
import os
import traceback


def emit(msg: dict):
    print(json.dumps(msg), flush=True)


def flatten_errors(error_logs) -> list:
    """Gradino returns a list (single table) or a dict {num_tables or "ablation": [errors]} (multi-table)."""
    if not error_logs:
        return []
    if isinstance(error_logs, dict):
        out = []
        for key, errs in error_logs.items():
            prefix = "[ablation]" if key == "ablation" else f"[{key} tables]"
            for err in errs or []:
                if err:
                    out.append(f"{prefix} {err}")
        return out
    return [str(e) for e in error_logs if e]


def serialize_samples(samples) -> dict:
    """Convert Gradino's {num_tables: {method: {perturbation: DataFrame}}} into JSON-serialisable records."""
    import pandas as pd

    output: dict = {}
    for nt_key in samples or {}:
        output[str(nt_key)] = {}
        for k1 in samples[nt_key]:
            output[str(nt_key)][k1] = {}
            for k2 in samples[nt_key][k1]:
                df = samples[nt_key][k1][k2]
                if not isinstance(df, pd.DataFrame):
                    print(f"[DEBUG] skipping non-DataFrame [{nt_key}][{k1}][{k2}]: {type(df).__name__}", file=sys.stderr, flush=True)
                    continue
                records = []
                for _, row in df.iterrows():
                    record: dict = {}
                    for col in df.columns:
                        val = row[col]
                        if isinstance(val, float) and val != val:  # NaN
                            record[col] = None
                        elif isinstance(val, (int, float, bool)):
                            record[col] = val
                        else:
                            s = str(val)
                            if s and s[0] in ('[', '{'):
                                try:
                                    record[col] = json.loads(s)
                                    continue
                                except Exception:
                                    pass
                            record[col] = s
                    records.append(record)
                if records:
                    output[str(nt_key)][k1][k2] = records
    return output


def count_records(output: dict) -> int:
    return sum(len(output[a][b][c]) for a in output for b in output[a] for c in output[a][b])


# ── Main generation logic ──────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        emit({"type": "error", "message": "No parameters provided"})
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        emit({"type": "error", "message": f"Invalid JSON params: {exc}"})
        sys.exit(1)

    # Set OpenAI API key
    api_key = params.get("api_key", "")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    gradino_path = os.environ.get("GRADINO_PATH", "/app/gradino")
    if gradino_path not in sys.path:
        sys.path.insert(0, gradino_path)
    # Gradino loads prompt/domain files with relative paths — must run from its own dir
    os.chdir(gradino_path)

    emit({"type": "status", "message": "Importing Gradino modules…"})

    try:
        from models import MTAutoGen  # noqa: E402
    except ImportError as exc:
        emit({"type": "error", "message": f"Failed to import Gradino: {exc}\n{traceback.format_exc()}"})
        sys.exit(1)

    emit({"type": "status", "message": "Starting generation…"})

    # Build args dict (Gradino expects a plain dict, not argparse.Namespace)
    args = {
        "domain": params.get("domain", "environmental"),
        "domain_description": params.get("domain_description") or "",
        "content_style": params.get("content_style") or "complex",
        "question_type": params.get("question_type", "sum"),
        "num_tables": int(params.get("num_tables", 3)),
        "num_samples": int(params.get("num_samples", 10)),
        "col_cardinality": int(params.get("col_cardinality", 20)),
        "num_columns": int(params.get("num_columns", 21)),
        "sequential": bool(params.get("sequential", False)),
        "perturbation_mode": params.get("perturbation_mode", "random"),
        "perturbations": params.get("perturbations") or [],
    }

    try:
        generator = MTAutoGen(args)
    except Exception as exc:
        emit({"type": "error", "message": f"Failed to initialise Gradino: {exc}", "traceback": traceback.format_exc()})
        sys.exit(1)

    num_samples = args["num_samples"]
    emit({"type": "status", "message": (
        f"Generating {num_samples} sample(s): num_tables={'ablation' if args['num_tables'] == -1 else args['num_tables']}, "
        f"method={args['question_type']}, domain={args['domain']}"
        + (f" ({args['domain_description'][:80]})" if args["domain_description"] else "")
        + f", content={args['content_style']}, sequential={args['sequential']}, "
        f"perturbations={args['perturbation_mode']}"
    )})
    emit({"type": "progress", "current": 0, "total": num_samples, "progress": 0.0, "desc": "Generating samples…"})

    all_errors: list = []
    produced = 0
    for i in range(num_samples):
        try:
            samples, error_logs = generator.run_generation(
                num_tables=args["num_tables"],
                method=args["question_type"],
                num_samples=1,
                domain=args["domain"],
                col_cardinality=args["col_cardinality"],
                num_columns=args["num_columns"],
                sequential=args["sequential"],
            )
            errors = flatten_errors(error_logs)
            data = serialize_samples(samples)
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            errors = [f"sample {i + 1}: {exc!r}"]
            data = {}

        all_errors.extend(errors)
        n_records = count_records(data)
        produced += n_records
        # emitted for every sample (even when empty) so that errors also survive a stop
        emit({"type": "sample", "data": data, "errors": errors})
        print(f"[DEBUG] sample {i + 1}/{num_samples}: {n_records} record(s), {len(errors)} error(s)", file=sys.stderr, flush=True)

        emit({
            "type": "progress",
            "current": i + 1,
            "total": num_samples,
            "progress": (i + 1) / num_samples,
            "desc": f"Generated {i + 1}/{num_samples} sample(s) · {produced} instance(s) so far",
        })

    emit({"type": "done", "errors": all_errors})


if __name__ == "__main__":
    main()
