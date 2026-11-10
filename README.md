# Social Media Reactions to Open Source Projects: A Study on AI projects on HackerNews

This repository contains the scripts, notebooks and datasets for our study of how Hacker News (HN) reacts to AI open-source projects hosted on GitHub (GH), and whether being shared on HN affects how those projects grow.

## Overview

We collected HN stories submitted between 2022-05-08 and 2024-05-09 that link to a GitHub repository, together with their comments. We split the stories into AI and non-AI using keywords in the title, then gathered the monthly GitHub activity of each linked repository (stars, forks, commits, pull requests and contributors).

| Part | Question | Main methods | Details |
| ---- | -------- | ------------ | ------- |
| Data collection | — | BigQuery (HN public dataset, GH Archive), GitHub API, keyword filtering | [src/data-collection/](src/data-collection/README.md) |
| RQ1 | What are the characteristics of AI projects shared on HN? | Descriptive statistics, temporal analysis, LDA topic modeling | [src/rq1/](src/rq1/README.md) |
| RQ2 | What is the sentiment of HN reactions to AI projects? | Human-labelled ground truth; fine-tuned BERT/RoBERTa vs. GPT-4o mini prompting; sentiment trends; AI vs. non-AI statistical tests | [src/rq2/](src/rq2/README.md) |
| RQ3 | How do GitHub metrics change after an HN submission, and does the HN sentiment matter? | Before/after comparison, statistical tests, growth by sentiment group | [src/rq3/](src/rq3/README.md) |
| RQ5 | Does an HN submission cause GitHub growth? | Treatment-control matching, difference-in-differences, event-study and placebo tests | [src/rq5/](src/rq5/README.md) |

Each folder's README explains its scripts, the order to run them in, and the schema of its datasets.

## Repository layout

```
src/
├── data-collection/   # Raw HN and GitHub datasets
├── rq1/               # Characteristics of AI projects on HN
├── rq2/               # Sentiment of HN reactions
├── rq3/               # GitHub metric changes after HN submission
└── rq5/               # Causal analysis (DiD)
```

Datasets used by each RQ are in its `dataset/` folder. Some large intermediate datasets are not included in the repository.

## Setup

- Python 3.11. Install the packages with `pip install -r requirements.txt` (a `venv` is recommended), or use `environment.yml` with conda.
- Most of the analysis is in Jupyter notebooks. Notebooks marked `[colab]` were run on Google Colab because of their computing requirements.
- GPT-4o mini prompting (RQ2) needs an OpenAI API key in a `.env` file.
- Scripts that call the GitHub API need a `GITHUB_TOKEN` environment variable.
- The BigQuery scripts in `src/data-collection/` need a Google Cloud project; replace `your_dataset` with your own dataset name.
