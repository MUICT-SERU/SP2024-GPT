# Social Media Reactions to Open Source Projects: A Study on AI projects on HackerNews
## Introduction
This README covers the following sections:
- The data collection section consists of the core retrieval scripts and datasets to be used across multiple parts of the research as explained in the data preparation section in our paper.
- The remaining RQ1-3 sections cover steps to preprocess the preliminary dataset and perform their respective analyses.
- See `requirements.txt` for the required Python packages. `venv` is recommended for Python package management.

## Data collection
The following sections describe the data collection process for the raw dataset. Note that any further processing of the raw data has been included in their respective RQ sections.

### Scripts
BigQuery dataset retrieval scripts:
- `retrieve-hn-stories.sql`: Script used to retrieve Hacker News stories using the public Hacker News dataset.
- `retrieve-hn-comments.sql`: Script used to retrieve Hacker News comments based on the retrieved Hacker News stories.
- `retrieve-gh-metrics.sql`: Script used to retrieve GitHub metrics using the public GitHub Archive dataset. Requires the `retrieve-hn-stories.sql` script to be run and for the dataset to be stored for referencing repository URL first.
- `retrieve-gh-metadata.sql`: Script used to retrieve GitHub metadata based on the retrieved Hacker News stories. Metadata such as repository creation date is required certain parts such as RQ3 when identifying projects that were created at least 6 months prior to HN submission.

Preliminary AI and GitHub repository filtering script:
- `ai_keywords.txt`: List of AI keywords used in the script, with each keyword separated by newline.
- `filter-ai-keywords.py`: Script used to filter only for stories whose title contain AI keywords defined in the `ai_keywords.txt` file.
- `filter-gh-repos.py`: Script used to filter only for stories containing GitHub repositories URLs.
- `remove-duplicate-urls.py`: Script used to remove entries containing duplicate GitHub repository URLs - selecting only the first story among the duplicates with the highest HN score. This is needed for RQ3 in order to not analyze duplicated GitHub repositories, but may find useful in general.

> Note: The AI and GitHub filtering were done directly within the data collection stage due to efficiency as these were used throughout our research.

### Schema

#### `hn_story-[tag].csv` – Hacker News Stories Data
Each tag denotes different filtering criteria on the dataset, which includes the following:
- `gh`: All stories containing GitHub repository URL.
- `gh-ai`: AI stories containing GitHub repository URL.
- `gh-ai-[no-dupes]`: AI stories containing GitHub repository URL with no duplicates GitHub repository. This is because multiple HN stories can reference the same repository URL. Non-duplicated dataset is used in RQ3 where we must consider unique repository to analyze their metrics.
- `gh-nonai`: Non-AI stories containing GitHub repository URL.
- `ghh-nonai-[no-dupes]`: Non-AI stories containing GitHub repository URL with no duplicates GitHub repository.

<!-- to add cumulative for DiD -->

| Attribute   | Description                                                               |
| ----------- | ------------------------------------------------------------------------- |
| `by`        | Username of the story's submitter.                                        |
| `dead`      | Indicates if the story is flagged as "dead" (removed). Empty if not dead. |
| `id`        | Unique identifier for the story.                                          |
| `score`     | Upvote count (popularity score).                                          |
| `text`      | Self-text content of the story (empty if URL-based).                      |
| `time`      | Unix epoch timestamp of submission time.                                  |
| `timestamp` | Human-readable UTC timestamp of submission.                               |
| `title`     | Title of the story.                                                       |
| `type`      | Post type (e.g., `story`, `poll`, etc.).                                  |
| `url`       | External URL linked in the story (if applicable).                         |

---

#### `hn_comment-[tag].csv` – Hacker News Comments Data
Same tags as the `hn_story-[tag].csv` dataset for each filtering criteria.

| Attribute      | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `comment_id`   | Unique identifier for the comment.                                 |
| `commenter`    | Username of the comment's author.                                  |
| `comment_text` | Text content of the comment.                                       |
| `comment_time` | UTC timestamp of when the comment was posted.                      |
| `parent_id`    | ID of the parent post (matches `story_id` for top-level comments). |
| `story_id`     | ID of the story the comment is associated with.                    |
| `story_title`  | Title of the linked story.                                         |

---

#### `metrics-[tag].csv` – Metrics data for projects.
Metric tags include the following:
- `hn-gh-ai`: Metric data for HN GH-AI stories.
- `hn-gh-ai-[6-months-before-after-hn]`: AI stories containing GitHub repository URL which has been created at least 6 months before HN submission as well as containing metrics 6 months afterwards. This is to ensure sufficient project activities, and was used for statistical analysis and DiD. Note that this **does not contain relative months** after HN submission, only a list of raw metrics for the repositories that fit the 6 months before and after criteria in the same format as the standard metrics file. This was generated by running `rq3/3a/filter-6months-before-after-hn.py`.

| Attribute            | Description                                                                |
| -------------------- | -------------------------------------------------------------------------- |
| `repo_full_name`     | Full name of the GitHub repository in the format `owner/repo`.             |
| `repo_url`           | URL link to the GitHub repository.                                         |
| `month`              | Monthly timestamp (YYYY-MM) indicating the time period of the metrics.     |
| `hn_submission_date` | Date and time when the repository was submitted to Hacker News (if any).   |
| `source`             | Source of submission information (e.g., "HN" for Hacker News).             |
| `hn_score`           | Hacker News score (upvotes minus flags) for the submission.                |
| `stars`              | Number of new GitHub stars the repository received in that month.          |
| `forks`              | Number of new forks created in that month.                                 |
| `commits`            | Number of commits made to the repository in that month.                    |
| `PRs`                | Number of pull requests opened in that month.                              |
| `contributors`       | Number of unique contributors active in that month.                        |
| `cumulative_stars`   | Total number of GitHub stars the repository has received up to that month. |
| `cumulative_forks`   | Total number of GitHub forks the repository has received up to that month. |

- `hn-gh-ai-5months-[no-dupes]`: Metric data for HN GH-AI stories which has been converted into relative 5 months after HN submission date. This was generated by running `rq3/3b-hn-effects-sentiment-growth/convert-to-relative-hn-date.py`. The relative metrics format is as follows:

| Attribute                             | Description                                                      |
| ------------------------------------- | ---------------------------------------------------------------- |
| `by`                                  | Username of the person who submitted the post on Hacker News.    |
| `discussion_id`                       | Unique identifier of the Hacker News discussion thread.          |
| `score`                               | Hacker News score (upvotes minus flags) at the time of scraping. |
| `timestamp`                           | Date and time when the Hacker News post was made.                |
| `title`                               | Title of the Hacker News submission.                             |
| `url`                                 | GitHub URL of the submitted repository.                          |
| `stars_at_submission`                 | GitHub stars at the time of Hacker News submission.              |
| `stars_month_1` to `_month_5`         | Stars gained in each of the first five months after submission.  |
| `commits_at_submission`               | Total commits in the repo at time of submission.                 |
| `commits_month_1` to `_month_5`       | Number of commits in each of the five months after submission.   |
| `pull_requests_at_submission`         | Total pull requests at submission time.                          |
| `pull_requests_month_1` to `_month_5` | Number of pull requests opened in each post-submission month.    |
| `forks_at_submission`                 | GitHub forks at the time of Hacker News submission.              |
| `forks_month_1` to `_month_5`         | Forks gained in each of the five months following submission.    |
| `contributors_at_submission`          | Number of contributors at the time of submission.                |
| `contributors_month_1` to `_month_5`  | Number of contributors in each post-submission month.            |

<!-- to add cumulative -->

### `metadata-[tag].csv` – Metadata for HN GH-AI projects.


| Attribute            | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `repo_full_name`     | GitHub repository identifier in `owner/repo` format. |
| `owner`              | GitHub username/organization owning the repository.  |
| `repo_name`          | Name of the GitHub repository.                       |
| `repo_creation_date` | UTC timestamp of repository creation.                |
| `contributor_count`  | Total contributors to the repository.                |
| `push_count`         | Number of pushes (commits) to the repository.        |
| `star_count`         | Number of GitHub stars.                              |
| `fork_count`         | Number of repository forks.                          |

> Note: In `metadata-[tags].csv`, Repository stats (`star_count`, `fork_count`, etc.) reflect historical snapshots at the time of data collection.

## RQ1a - GitHub Repository Creation Distribution
- `analyze-gh-repo-creation-date.ipynb`: Analyze the distribution of GitHub repository creation dates.

## RQ1b - GitHub Hacker News Username Analysis
- `analyze-gh-usernames.ipynb`: Analyze the number of GitHub repository owners who self-promote their project on Hacker News.

## RQ1c - Temporal Analysis
- `analyze-hn-stories.ipynb`: Visualize the number of Hacker News stories over time and keyword distribution.
- `analyze-hn-comments.ipynb`: Analyze Hacker News comments based on the HN GH-AI stories.

## RQ1d - Topic Modeling
- `analyze-hn-stories-lda-[colab].ipynb`: Perform topic modeling on Hacker News stories to identify dominant topics. This has been executed in Google Colab due to the heavy computational requirements from LDA.

## RQ2a - Creating Ground Truth for Sentiment Analysis Evaluation
- `sample-hn-comments-stratified.py`: Sample comments using stratified sampling from the HN AI comments.

## RQ2b - Finetuning Pre-trained Transformers (Finding the Best Sentiment Analysis Method)
- `finetuning-bert-hn-comment-[colab].ipynb`: Fine-tune BERT on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-bert-hn-story-[colab].ipynb`: Fine-tune BERT on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-roberta-hn-comment-[colab].ipynb`: Fine-tune RoBERTa on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-roberta-hn-story-[colab].ipynb`: Fine-tune RoBERTa on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-twitter-roberta-hn-comment-[colab].ipynb`: Fine-tune Twitter RoBERTa on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-twitter-roberta-hn-story-[colab].ipynb`: Fine-tune Twitter RoBERTa on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.

## RQ2b - Prompting GPT-4o mini (Finding the Best Sentiment Analysis Method)
- `prompting-gpt-hn-ai-comment.ipynb`: Prompt GPT-4o mini to output sentiment and reason, and evaluate performance using weighted F1-score on the comment ground truth.
- `prompting-gpt-hn-ai-story.ipynb`: Prompt GPT-4o mini to output sentiment and reason, and evaluate performance using weighted F1-score on the story ground truth.

## RQ2c - Sentiment Analysis
- `hn_gh_ai_story_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH-AI story.
- `hn_gh_ai_comment_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH-AI comment.
- `hn_gh_non_ai_story_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH story with no AI keywords.
- `hn_gh_non_ai_comment_sentiment_analysis.ipynb`: Perform sentiment analysis on all comments in the HN GH story with no AI keywords.

## RQ2d - Sentiment and Reaction Trend Analysis
- `analyze-sentiment-result.ipynb`: Visualize the story and comment sentiment results using area stacks and reaction using a heatmap.

## RQ2e - Statistical Test
- `statistical-test.ipynb`: Perform statistical tests between the HN GH-AI story and comment and the HN GH story and comment with no AI keywords.

## RQ2 Dataset Schema
- Consists of all CSV datasets used or created from scripts inside rq2

### `ground_truth_hn_ai_[data].csv` - Ground Truth Data
Data can either be:
- `story`: Hacker News story
- `comment`: Hacker News comment

| Attribute          | Description                                    |
| ------------------ | ---------------------------------------------- |
| `discussion_id`    | ID of Hacker News story                        |
| `title`            | Title of the story                             |
| `url`              | External URL linked in the story               |
| `discussion_date`  | Date and time of story submission              |
| `comment_id`       | ID of Hacker News comment                      |
| `comment_text`     | Text content of the comment                    |
| `comment_date`     | Date and time of when the comment was posted   |
| `hu1_[data]_label` | Human investigator No.1 `[data]` label         |
| `hu2_[data]_label` | Human investigator No.2 `[data]` label         |
| `[data]_match`     | Matching of `[data]` between hu1 and hu2 label |
| `[data]_consensus` | Final `[data]` consensus label                 |

---

### `sampled_hn_ai_story_gpt_sentiment` - Output of GPT-4o mini on Story Ground Truth Data

| Attribute                  | Description                                              |
| -------------------------- | -------------------------------------------------------- |
| `discussion_id`            | ID of Hacker News story                                  |
| `title`                    | Title of the story                                       |
| `url`                      | External URL linked in the story                         |
| `discussion_date`          | Date and time of story submission                        |
| `hu1_story_label`          | Human investigator No.1 story label                      |
| `hu2_story_label`          | Human investigator No.2 story label                      |
| `story_match`              | Matching of the story between hu1 and hu2 label          |
| `story_consensus`          | Final story consensus label                              |
| `senti_prompt0_2shot_gpt`  | Story sentiment towards AI from GPT-4o mini              |
| `reason_prompt0_2shot_gpt` | Reason for the assigned story sentiment from GPT-4o mini |

---

### `sampled_hn_ai_comment_gpt_sentiment.csv` - Output of GPT-4o mini on Comment Ground Truth Data

| Attribute                          | Description                                                |
| ---------------------------------- | ---------------------------------------------------------- |
| `discussion_id`                    | ID of Hacker News story                                    |
| `title`                            | Title of the story                                         |
| `url`                              | External URL linked in the story                           |
| `discussion_date`                  | Date and time of story submission                          |
| `comment_id`                       | ID of Hacker News comment                                  |
| `comment_text`                     | Text content of the comment                                |
| `comment_date`                     | Date and time of when the comment was posted               |
| `hu1_comment_label`                | Human investigator No.1 comment label                      |
| `hu2_comment_label`                | Human investigator No.2 comment label                      |
| `comment_match`                    | Matching of the comment between hu1 and hu2 label          |
| `comment_consensus`                | Final comment consensus label                              |
| `story_consensus`                  | Final story consensus label                                |
| `senti_comment_prompt2_1shot_gpt`  | Comment sentiment towards AI from GPT-4o mini              |
| `reason_comment_prompt2_1shot_gpt` | Reason for the assigned comment sentiment from GPT-4o mini |

---

### `hn_gh_ai_story_sentiment.csv` - Story Sentiment and Reason from GPT-4o mini on HN-GH AI Story Dataset

| Attribute                | Description                                              |
| ------------------------ | -------------------------------------------------------- |
| `story_id`               | ID of Hacker News story                                  |
| `title`                  | Title of the story                                       |
| `url`                    | External URL linked in the story                         |
| `datetime`               | Unix epoch timestamp of story submission time.           |
| `story_sentiment`        | Story sentiment towards AI from GPT-4o mini              |
| `story_sentiment_reason` | Reason for the assigned story sentiment from GPT-4o mini |

---

### `hn_gh_ai_comment_sentiment.csv` - Comment Sentiment and Reason from GPT-4o mini on HN GH-AI Comment Dataset

| Attribute                  | Description                                                |
| -------------------------- | ---------------------------------------------------------- |
| `comment_id`               | ID of Hacker News comment                                  |
| `comment_text`             | Text content of the comment                                |
| `comment_datetime`         | Unix epoch timestamp of comment posted time.               |
| `story_id`                 | ID of Hacker News story                                    |
| `story_title`              | Title of the story                                         |
| `url`                      | External URL linked in the story                           |
| `story_datetime`           | Unix epoch timestamp of story submission time.             |
| `comment_sentiment`        | Comment sentiment towards AI from GPT-4o mini              |
| `comment_sentiment_reason` | Reason for the assigned comment sentiment from GPT-4o mini |
| `story_sentiment`          | Story sentiment towards AI from GPT-4o mini                |
| `story_sentiment_reason`   | Reason for the assigned story sentiment from GPT-4o mini   |

---

### `hn_gh_non_ai_story_sentiment.csv` - Story Sentiment and Reason from GPT-4o mini on HN GH Story Dataset with No AI Keywords

| Attribute                | Description                                              |
| ------------------------ | -------------------------------------------------------- |
| `story_id`               | ID of Hacker News story                                  |
| `title`                  | Title of the story                                       |
| `url`                    | External URL linked in the story                         |
| `datetime`               | Unix epoch timestamp of story submission time.           |
| `story_sentiment`        | Story sentiment towards technology from GPT-4o mini      |
| `story_sentiment_reason` | Reason for the assigned story sentiment from GPT-4o mini |

---

### `hn_gh_non_ai_comment_sentiment.csv` - Comment Sentiment and Reason from GPT-4o mini on All Comments Replied to HN GH Story Dataset with No AI Keywords

| Attribute                  | Description                                                |
| -------------------------- | ---------------------------------------------------------- |
| `comment_id`               | ID of Hacker News comment                                  |
| `comment_text`             | Text content of the comment                                |
| `comment_datetime`         | Unix epoch timestamp of comment posted time.               |
| `story_id`                 | ID of Hacker News story                                    |
| `story_title`              | Title of the story                                         |
| `url`                      | External URL linked in the story                           |
| `story_datetime`           | Unix epoch timestamp of story submission time.             |
| `comment_sentiment`        | Comment sentiment towards technology from GPT-4o mini      |
| `comment_sentiment_reason` | Reason for the assigned comment sentiment from GPT-4o mini |

## RQ3a - Historical Metrics
- `analyze-historical-metrics.ipynb`: Analyze historical GitHub repository metrics over time. Initially filters outlier repositories prior to the analysis.
- `stats-test-metrics.ipynb`: Perform statistical tests on the historical metrics data on the metric changes after HN submission. Initially filters for repositories that contain metrics at minimum 6 months before and after HN submission to ensure a sufficient time frame for repository activity.

## RQ3b - Metric growth analysis based on Hacker News sentiment
Perform analysis and visualization on GitHub metric data base on their respective sentiment on Hacker News to find the relationship between Hacker News sentiment and GitHub metric growth

### Scripts explaination and run order
1. `average_comment_sentiment_Calculator.ipynb`
    - Merge Hacker News comment dataset file into story dataset file via parent story ID
    - Filter out stories without comment or have link to the same GitHub repository leaving out only the oldest one
    - Calculate average comment sentiment of each story and classify overall sentiment from the result (positive, neutral, negative)
2. `file_merger.ipynb`
    - Merge Hacker News dataset file with GitHub dataset file via story URL
    - Display amount of data
3. `metric_value_processor.ipynb`
    - Calculate accumulative value of each metric (exception being contributors)
    - Calculate distant value in between each month as both raw and percentage
4. `sentiment_categorizer.ipynb`
    - Categorize dataset base on sentiment (positive, neutral, negative) into seperate files
    - Display amount of data in each group/file
5. `outliers_filter.ipynb`
    - Remove outliers of each sentiment group using IQR method
- `metric_mean_display.ipynb` (optional)
    - Return or display mean values of metric values in each sentiment group
6. `visualizer.ipynb`
    - Visualize the data as box plot (median) and point plot (mean)

### Schema explanation
#### `metrics-hn-gh-ai-5months-[no-dupes].csv`
This contains the HN GH-AI repository metrics converted into relative 5 months from the Hacker News submission date for each story. Month 0 denotes the month of Hacker News submission, month 1 denotes the month after the Hacker News submission, and so on. No duplicated repositories are included as some stories contain the same repository URL.

| Attribute      | Description      |
| ------------- | ------------- |
| by | Owner of Hacker News discussion |
| discussion_id | ID of Hacker News discussion |
| timestamp | Date and time of posting |
| title | Discussion title |
| url | Link of a GitHub repository that the discussion refers to |
| __[metric]__\_at_submission | Total value of a specific GitHub repository's __[metric]__ at the time of the Hacker News Discussion has been posted|
| __[metric]__\_at_month\_ __[number]__ | Additional value of GitHub repository's __[metric]__ at __[number]__ month after the Hacker News Discussion has been posted|

#### hn_gh_ai_story_sentiment.csv
| Attribute      | Description      |
| ------------- | ------------- |
| discussion_id | ID of Hacker News discussion |
| title | Discussion title |
| url | Link of a GitHub repository that the discussion refers to |
| datetime | Date and time of posting |
| story_sentiment | Sentiment of the discussion title (positive: 1, neutral: 0, negative: -1) |
| story_sentiment_reason | Reason why the discussion title has such sentiment |

#### hn_gh_ai_story_sentiment.csv
| Attribute      | Description      |
| ------------- | ------------- |
| comment_id | ID of Hacker News comment |
| commenter | User that posted the comment |
| comment_text | Text or words of comment |
| comment_datetime | Date and time that the comment has been posted |
| story_id | ID of comment's parent discussion |
| story_title | Title of comment's parent discussion |
| url | Link of a GitHub repository that comment's parent discussion refers to |
| story_date | Date and time that comment's parent discussion has been posted |
| comment_sentiment | Sentiment of the comment (positive: 1, neutral: 0, negative: -1) |
| comment_sentiment_reason | Reason why the discussion title has such sentiment |

#### sentiments_df.csv
| Attribute      | Description      |
| ------------- | ------------- |
| discussion_id | ID of Hacker News discussion |
| title | Discussion title |
| url | Link of a GitHub repository that the discussion refers to |
| datetime | Date and time of posting |
| story_sentiment | Sentiment of the discussion title (positive: 1, neutral: 0, negative: -1) |
| story_sentiment_reason | Reason why the discussion title has such sentiment |
| average_comments_sentiment | Average sentiment value of the discussion's comments (story has no comment: -2) |
| overall_comments_sentiment | Overall sentiment of the discussion as a whole (Positive: 1, Neutral: 0, Negative: -1, Story has no comment: -2) |

#### join_result.csv, Positive_stories.csv, Neutral_stories.csv, Negative_stories.csv, final_result.csv
| Attribute      | Description      |
| ------------- | ------------- |
| by | Owner of Hacker News discussion |
| discussion_id | ID of Hacker News discussion |
| timestamp | Date and time of posting |
| title | Discussion title |
| url | Link of a GitHub repository that the discussion refers to |
| __[metric]__\_at_submission | Total value of a specific GitHub repository's __[metric]__ at the time of the Hacker News Discussion has been posted|
| __[metric]__\_at_month\_ __[number]__ | Additional value of GitHub repository's __[metric]__ at __[number]__ month after the Hacker News Discussion has been posted|
| average_comments_sentiment | Average sentiment value of the discussion's comments |
| overall_comments_sentiment | Sentiment value of the discussion as a whole (Positive: 1, Neutral: 0, Negative: -1) |
| dist\_ __[metric]__(__[time_period1]__-__[time_period2]__) | Raw change in __[metric]__ in between time of __[time_period1]__ and __[time_period2]__ after the Hacker News Discussion has been posted |
| percent\_ __[metric]__(__[time_period1]__-__[time_period2]__) | Percentage change in __[metric]__ in between time of __[time_period1]__ and __[time_period2]__ after the Hacker News Discussion has been posted |
| sentiment | text version of overall_comments_sentiment (Positive, Neutral, Negative) |