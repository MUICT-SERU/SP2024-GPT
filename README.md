# Social Media Reactions to Open Source Projects: A Study on AI projects on HackerNews

This repository contains the scripts, notebooks and datasets for our study of how Hacker News (HN) reacts to AI open-source projects hosted on GitHub (GH), and whether being shared on HN affects how those projects grow.

## Paper

This is the replication package for our ICSME 2025 paper:

> Prachnachai Meakpaiboonwattana, Warittha Tarntong, Thai Mekratanavorakul, Chaiyong Ragkhitwetsagul, Pattaraporn Sangaroonsilp, Raula Gaikovina Kula, Morakot Choetkiertikul, Kenichi Matsumoto, and Thanwadee Sunetnanta. **"Social Media Reactions to Open Source Promotions: AI-Powered GitHub Projects on Hacker News."** In *Proceedings of the 2025 IEEE International Conference on Software Maintenance and Evolution (ICSME)*, pp. 344–355, 2025. [[IEEE CSDL]](https://www.computer.org/csdl/proceedings-article/icsme/2025/958700a344/2bgfY8Q81TG) [[arXiv]](https://arxiv.org/abs/2506.12643)

It also contains the material for the extended version of the paper, which is currently under review at ACM Transactions on Software Engineering and Methodology (TOSEM).

```bibtex
@inproceedings{meakpaiboonwattana2025social,
  title     = {Social Media Reactions to Open Source Promotions: AI-Powered GitHub Projects on Hacker News},
  author    = {Meakpaiboonwattana, Prachnachai and Tarntong, Warittha and Mekratanavorakul, Thai and Ragkhitwetsagul, Chaiyong and Sangaroonsilp, Pattaraporn and Kula, Raula Gaikovina and Choetkiertikul, Morakot and Matsumoto, Kenichi and Sunetnanta, Thanwadee},
  booktitle = {Proceedings of the 2025 IEEE International Conference on Software Maintenance and Evolution (ICSME)},
  pages     = {344--355},
  year      = {2025}
}
```

## Overview

We collected HN stories submitted between 2022-05-08 and 2024-05-09 that link to a GitHub repository, together with their comments. We split the stories into AI and non-AI using keywords in the title, then gathered the monthly GitHub activity of each linked repository (stars, forks, commits, pull requests and contributors).

| Part | Research question | Main methods | Details |
| ---- | -------- | ------------ | ------- |
| Data collection | — | BigQuery (HN public dataset, GH Archive), GitHub API, keyword filtering | [src/data-collection/](src/data-collection/README.md) |
| RQ1 | What is the spread of GitHub AI project stories on Hacker News? | Descriptive statistics, temporal analysis, LDA topic modeling | [src/rq1/](src/rq1/README.md) |
| RQ2 | What are the social reactions to HN GH-AI stories? | Human-labelled ground truth; fine-tuned BERT/RoBERTa vs. GPT-4o mini prompting; sentiment trends; AI vs. non-AI statistical tests | [src/rq2/](src/rq2/README.md) |
| RQ3 | What are the changes of activities in GitHub AI projects after being mentioned in Hacker News? | Before/after comparison, statistical tests, growth by sentiment group | [src/rq3/](src/rq3/README.md) |
| RQ5 *(TOSEM extension)* | Does an HN submission cause GitHub growth? | Treatment-control matching, difference-in-differences, event-study and placebo tests | [src/rq5/](src/rq5/README.md) |

RQ1–RQ3 are the research questions of the ICSME 2025 paper. RQ5 is part of the extended TOSEM version. Each folder's README explains its scripts, the order to run them in, and the schema of its datasets.

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
