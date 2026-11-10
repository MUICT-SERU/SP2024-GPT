# Data Collection

Scripts that build the raw datasets used by every RQ: Hacker News (HN) stories and comments, and the monthly GitHub (GH) metrics and metadata of the repositories they link to. Further processing is done inside each RQ folder.

## Scripts
BigQuery dataset retrieval scripts:
- `1-hn/retrieve-hn-stories.sql`: Script used to retrieve Hacker News stories (2022-05-08 to 2024-05-09) using the public Hacker News dataset.
- `1-hn/retrieve-hn-comments.sql`: Script used to retrieve Hacker News comments based on the retrieved Hacker News stories.
- `2-gh-metrics/retrieve-gh-metrics.sql`: Script used to retrieve monthly GitHub metrics using the public GitHub Archive dataset. Requires the `retrieve-hn-stories.sql` script to be run and for the dataset to be stored for referencing repository URL first.
- `2-gh-metrics/retrieve-gh-metadata.sql`: Script used to retrieve GitHub metadata based on the retrieved Hacker News stories. Metadata such as repository creation date is required certain parts such as RQ3 when identifying projects that were created at least 6 months prior to HN submission.

Preliminary AI and GitHub repository filtering scripts (`1-hn/`):
- `filter-gh-stories.py`: Script used to filter only for stories whose URL is a GitHub repository root URL (`github.com/owner/repo`).
- `filter-ai-stories.py`: Script used to filter only for stories whose title contains an AI keyword (whole-word match), producing `hn-stories-gh-ai.csv`. It reads the keyword list from `ai_keywords.txt` in the working directory.
- `filter-nonai-stories.py`: Script used to filter only for stories whose title contains no AI keyword, producing `hn-stories-gh-nonai.csv`. It reads the keyword list from `rq1_ai_keywords.txt`.
- `filter-comments-stories_id.py`: Script used to keep only the comments that belong to the filtered stories (e.g., `hn-comments-gh-ai.csv`).
- `combine-csvs.py`: Helper script used to concatenate two CSV files.

> Note: The AI keyword list (one keyword per line) is stored at [`rq1_ai_keywords.txt`](../rq1/1c-temporal-analysis/story/rq1_ai_keywords.txt) (in RQ1). Copy it next to the filtering scripts (as `ai_keywords.txt` for `filter-ai-stories.py`) before running them.

GitHub repository scripts (`2-gh-metrics/`):
- `remove-duplicate-urls.py`: Script used to remove entries containing duplicate GitHub repository URLs - selecting only the first story among the duplicates with the highest HN score. This is needed for RQ3 in order to not analyze duplicated GitHub repositories, but may find useful in general.
- `filter-nonhn-gh-ai/filter.py`: Script used to select candidate AI control repositories (not submitted to HN) whose repository name contains an AI keyword (substring match, e.g., `-ai-`, `-llm-`).
- `filter-nonhn-gh-ai/filter-strict.py`: Same as `filter.py` but uses strict whole-word keyword matching.

Other scripts:
- `metadata.py`: Fetch current cumulative metrics (stars, forks, contributors, commits, PRs) for a list of repositories using the GitHub REST and GraphQL APIs. Requires a `GITHUB_TOKEN` environment variable; run with `--input <csv with repo_full_name> --output <csv>`. The script is resumable.

> Note: The AI and GitHub filtering were done directly within the data collection stage due to efficiency as these were used throughout our research.

## Schema

### `hn_story-[tag].csv` – Hacker News Stories Data
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

### `hn_comment-[tag].csv` – Hacker News Comments Data
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

### `metrics-[tag].csv` – Metrics data for projects.
Metric tags include the following:
- `hn-gh-ai`: Metric data for HN GH-AI stories.
- `hn-gh-ai-[6-months-before-after-hn]`: AI stories containing GitHub repository URL which has been created at least 6 months before HN submission as well as containing metrics 6 months afterwards. This is to ensure sufficient project activities, and was used for statistical analysis and DiD. Note that this **does not contain relative months** after HN submission, only a list of raw metrics for the repositories that fit the 6 months before and after criteria in the same format as the standard metrics file. This was generated by running [`filter-6months-before-after-hn.py`](../rq3/3a-historical-metrics/refilter/filter-6months-before-after-hn.py) (in RQ3).

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

- `hn-gh-ai-5months-[no-dupes]`: Metric data for HN GH-AI stories which has been converted into relative 5 months after HN submission date. This was generated by running [`convert-to-relative-hn-date.py`](../rq3/3b-hn-effects-sentiment-growth/convert-to-relative-hn-date.py) (in RQ3). The relative metrics format is as follows:

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
