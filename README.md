# Social Media Reactions to Open Source Projects: A Study on AI projects on HackerNews
## Introduction
This README covers the following sections:
- The data collection section consists of the core retrieval scripts and datasets to be used across multiple parts of the research as explained in the data preparation section in our paper.
- The remaining RQ1-3 sections cover steps to preprocess the preliminary dataset for their respective analyses.

## Data collection
The following sections describe the data collection process for the raw dataset. Note that any further processing of the raw data has been included in their respective RQ sections.

### Scripts
BigQuery dataset retrieval scripts:
- `retrieve-hn-stories.sql`: script used to retrieve Hacker News stories using the public Hacker News dataset.
- `retrieve-hn-comments.sql`: script used to retrieve Hacker News comments based on the retrieved Hacker News stories.
- `retrieve-gh-metrics.sql`: script used to retrieve GitHub metrics using the public GitHub Archive dataset. Requires the `retrieve-hn-stories.sql` script to be run and for the dataset to be stored for referencing repository URL first.
- `retrieve-gh-metadata.sql`: script used to retrieve GitHub metadata based on the retrieved Hacker News stories. Metadata such as repository creation date is required certain parts such as RQ3 when identifying projects that were created at least 6 months prior to HN submission.

Preliminary AI and GitHub repository filtering script:
- `ai_keywords.txt`: list of AI keywords used in the script, with each keyword separated by newline.
- `filter-ai-keywords.py`: script used to filter only for stories whose title contain AI keywords defined in the `ai_keywords.txt` file.
- `filter-gh-repos.py`: script used to filter only for stories containing GitHub repositories URLs.

### Schema

#### `hn_story-[tag].csv` – Hacker News Stories Data
Each tag denotes different filtering criteria on the dataset, which includes the following:
- `gh`: All stories containing GitHub repository URL.
- `gh-ai`: AI stories containing GitHub repository URL.
- `gh-nonai`: Non-AI stories containing GitHub repository URL.

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

#### `metrics-[tag].csv` – Hacker News Stories with GitHub Links
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

> Note: In `metrics-[tags].csv`, Repository stats (`star_count`, `fork_count`, etc.) reflect historical snapshots at the time of data collection.

## RQ1a - GitHub Repository Creation Distribution

### Scripts explaination and run order
- `analyze-gh-repo-creation-date.ipynb`: Analyze the distribution of GitHub repository creation dates.

## RQ1b - GitHub Hacker News Username Analysis
- `analyze-gh-usernames.ipynb`: Analyze the number of GitHub repository owners who self-promote their project on Hacker News.

## RQ1c - Temporal Analysis
- `analyze-hn-stories.ipynb`: Visualize the number of Hacker News stories over time and keyword distribution.
- `analyze-hn-comments.ipynb`: Analyze Hacker News comments based on the HN GH-AI stories.

## RQ1d - Topic Modeling
- `analyze-hn-stories-lda.ipynb`: Perform topic modeling on Hacker News stories to identify dominant topics.

## RQ3a - Historical Metrics
- `analyze-historical-metrics.ipynb`: Analyze historical GitHub repository metrics over time. Initially filters outlier repositories prior to the analysis.
- `stats-test-metrics.ipynb`: Perform statistical tests on the historical metrics data on the metric changes after HN submission.

## RQ3b - Metric growth analysis based on Hacker News sentiment
Perform analysis and visualization on GitHub metric data base on their respective sentiment on Hacker News to find the relationship between Hacker News sentiment and GitHub metric growth
### Scripts explaination and run order
#### 1. average_comment_sentiment_Calculator.ipynb
- Merge Hacker News comment dataset file into story dataset file via parent story ID
- Filter out stories without comment or have link to the same GitHub repository leaving out only the oldest one
- Calculate average comment sentiment of each story and classify overall sentiment from the result (positive, neutral, negative)
#### 2. file_merger.ipynb
- Merge Hacker News dataset file with GitHub dataset file via story URL
- Display amount of data
#### 3. metric_value_processor.ipynb
- Calculate accumulative value of each metric (exception being contributors)
- Calculate distant value in between each month as both raw and percentage
#### 4. sentiment_categorizer.ipynb
- Categorize dataset base on sentiment (positive, neutral, negative) into seperate files
- Display amount of data in each group/file
#### 5. outliers_filter
- Remove outliers of each sentiment group using IQR method
#### - metric_mean_display.ipynb (optional)
- Return or display mean values of metric values in each sentiment group
#### 6. visualizer.ipynb
- Visualize the data as box plot (median) and point plot (mean)

### Schema explanation
#### hn-stories-gh-ai-metrics-5months-[no-dupes]-v4-monthly-new.csv
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