# RQ1: What is the spread of GitHub AI project stories on Hacker News?

Descriptive analysis of HN GH-AI stories: when the repositories were created, whether submitters promote their own projects, how stories and comments change over time, and what topics they cover.

## RQ1a - GitHub Repository Creation Distribution
Folder: [`1a-gh-creation-dist/`](1a-gh-creation-dist/)

- `analyze-gh-creation-dist.ipynb`: Analyze the distribution of GitHub repository creation dates.

## RQ1b - GitHub Hacker News Username Analysis
Folder: [`1b-gh-hn-username/`](1b-gh-hn-username/)

- `analyze-hn-gh-username.ipynb`: Analyze the number of GitHub repository owners who self-promote their project on Hacker News.

## RQ1c - Temporal Analysis
Folder: [`1c-temporal-analysis/`](1c-temporal-analysis/)

- `story/analyze-hn-stories.ipynb`: Visualize the number of Hacker News stories over time and keyword distribution.
- `story/rq1_ai_keywords.txt`: List of AI keywords, one per line, used for the AI story filtering and the keyword distribution.
- `comment/analyze-hn-comments.ipynb`: Analyze Hacker News comments based on the HN GH-AI stories.

## RQ1d - Topic Modeling
Folder: [`1d-topic-modelling/`](1d-topic-modelling/)

- `analyze-hn-stories-lda.ipynb`: Perform topic modeling on Hacker News stories to identify dominant topics.
- `analyze-hn-stories-lda-[colab].ipynb`: Google Colab version of the topic modeling notebook, used due to the heavy computational requirements from LDA.

## RQ1 Dataset
Folder: [`dataset/`](dataset/)

- `hn-stories-gh-ai-metadata.csv`: HN GH-AI stories joined with their GitHub repository metadata (see the `metadata-[tag].csv` schema).
