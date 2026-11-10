# TabgenQA

A web-based demo for generating tabular Question-Answering benchmarks, powered by Gradino. Accepted at CIKM 2026 demo track.  
For any help setting up the system, open a Github issue or write to `micheleluca.contalbo@unimore.it`

## Features

- **Parameter configuration**: set domain, question type, table count, sample count, cardinality, and column count
- **Live progress**: real-time progress bar and status updates during generation
- **Stop control**: cancel a running generation at any time
- **Instance editor**: edit questions, answers, and tables (cell values, hierarchical headers, schema changes, add/remove rows & columns)
- **Export**: download the dataset as CSV or JSON

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)
- An **OpenAI API key** (Gradino uses GPT for table and question generation)

### Run

```bash
git clone https://github.com/softlab-unimore/TabgenQA.git
cd TabgenQA

# Optional: set API key via .env (or enter it in the UI at runtime)
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

docker compose up --build
```

Then open **http://localhost:8000** in your browser.

> The first build clones Gradino and installs all dependencies (including z3-solver). This may take 3–5 minutes. Subsequent starts are faster.

## Usage

1. **Enter your OpenAI API key** in the top-right field (if not set via `.env`)
2. **Configure parameters** in the left panel:
   | Parameter | Description |
   |-----------|-------------|
   | Domain | Domain for few-shot table examples (environmental / finance / healthcare / products) |
   | Question Type | Aggregation type: sum, average, or superlative |
   | Number of Tables | Tables per instance |
   | Num Samples | How many instances to generate |
   | Col. Cardinality | Cardinality of the Gradino's latent relational source |
   | Num Columns | Number of columns in Gradino's latent relational source |
   | Sequential | Enable multi-hop questions across tables via foreign keys |
3. Click **Generate Benchmark**
4. Watch the progress bar; click **Stop** to cancel at any time
5. Once complete, click the **pencil icon** on any instance to edit:
   - **Question & Answer tab**: edit the question text and expected answer
   - **Tables tab**: full table editor: click cells to select, double-click to edit, use the toolbar to add/remove rows and columns, adjust colspan/rowspan for hierarchical headers
6. **Download** the final dataset as CSV or JSON
7. or **Evaluate** the models on the created datasets and analyze their performance in the **Leaderboard** tab

## Citation

```
@inproceedings{10.1145/3799682.3840263,
author = {Contalbo, Michele Luca and Paganelli, Matteo and Papotti, Paolo and Guerra, Francesco},
title = {TabgenQA: A Platform for Non-Relational, Multi-Tabular, Numerical QA Benchmark Generation and LLM Evaluation},
year = {2026},
isbn = {9798400725395},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3799682.3840263},
doi = {10.1145/3799682.3840263},
abstract = {Large language models (LLMs) are widely used for tabular data analysis, but their performance often does not transfer from standard Table QA benchmarks to real-world settings, where tables are typically non-relational, with hierarchical headers, merged cells, inconsistent units, noise, and implicit cross-table dependencies. We present name, an interactive system built on top of gradino for generating verifiable non-relational multi-table QA benchmarks and evaluating LLMs on them. Users configure domain-specific benchmark settings, inspect and refine generated instances, and compare API-based or locally deployed models through live leaderboards and error analysis views. Across procurement, failure diagnosis, and benchmark curation scenarios, name provides an end-to-end workflow for deployment-oriented assessment of LLMs on real-world tabular data.},
booktitle = {Proceedings of the 35th ACM International Conference on Information and Knowledge Management},
pages = {9102–9107},
numpages = {6},
keywords = {benchmark generation, llm evaluation, tabular data analysis},
location = {Rome, Italy},
series = {CIKM '26}
}
```
