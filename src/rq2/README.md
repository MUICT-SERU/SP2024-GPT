# RQ2: What are the social reactions to HN GH-AI stories?

Selects a sentiment classifier using a human-labelled ground truth (fine-tuned transformers vs. GPT-4o mini prompting), applies the best one (GPT-4o mini) to all AI and non-AI stories and comments, analyses the trends, compares AI with non-AI, and validates the results manually.

## RQ2a - Creating Ground Truth for Sentiment Analysis Evaluation
Folder: [`2a-ground-truth-eval/`](2a-ground-truth-eval/)

- `sample-hn-comments-stratified.py`: Sample comments using stratified sampling from the HN AI comments.
- `analyze-sampled-dataset.ipynb`: Analyze the sampled ground truth dataset.

## RQ2b - Finetuning Pre-trained Transformers (Finding the Best Sentiment Analysis Method)
Folder: [`2b-finetuning-transformers/`](2b-finetuning-transformers/)

- `finetuning-bert-hn-comment-[colab].ipynb`: Fine-tune BERT on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-bert-hn-story-[colab].ipynb`: Fine-tune BERT on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-roberta-hn-comment-[colab].ipynb`: Fine-tune RoBERTa on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-roberta-hn-story-[colab].ipynb`: Fine-tune RoBERTa on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-twitter-roberta-hn-comment-[colab].ipynb`: Fine-tune Twitter RoBERTa on the comment ground truth and evaluate performance using 5-fold cross-validation in Google Colab.
- `finetuning-twitter-roberta-hn-story-[colab].ipynb`: Fine-tune Twitter RoBERTa on the story ground truth and evaluate performance using 5-fold cross-validation in Google Colab.

## RQ2b - Prompting GPT-4o mini (Finding the Best Sentiment Analysis Method)
Folder: [`2b-prompting-gpt/`](2b-prompting-gpt/)

- `prompting-gpt-hn-ai-comment.ipynb`: Prompt GPT-4o mini to output sentiment and reason, and evaluate performance using weighted F1-score on the comment ground truth.
- `prompting-gpt-hn-ai-story.ipynb`: Prompt GPT-4o mini to output sentiment and reason, and evaluate performance using weighted F1-score on the story ground truth.

## RQ2c - Sentiment Analysis
Folder: [`2c-sentiment-analysis/`](2c-sentiment-analysis/)

- `hn_gh_ai_story_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH-AI story.
- `hn_gh_ai_comment_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH-AI comment.
- `hn_gh_non_ai_story_sentiment_analysis.ipynb`: Perform sentiment analysis on the HN GH story with no AI keywords.
- `hn_gh_non_ai_comment_sentiment_analysis.ipynb`: Perform sentiment analysis on all comments in the HN GH story with no AI keywords.
- `preprocess_comment_text.ipynb`: Clean comment text in the sentiment result files (remove HTML tags, decode HTML entities, trim whitespace). Overwrites the input file in place.

## RQ2d - Sentiment and Reaction Trend Analysis
Folder: [`2d-reaction-trend-analysis/`](2d-reaction-trend-analysis/)

- `analyze-sentiment-result.ipynb`: Visualize the story and comment sentiment results using area stacks and reaction using a heatmap. Output figures are saved in `plots/`.

## RQ2e - Statistical Test
Folder: [`2e-statistical-test/`](2e-statistical-test/)

- `statistical-test.ipynb`: Perform statistical tests between the HN GH-AI story and comment and the HN GH story and comment with no AI keywords.

## RQ2f - Manual Validation of GPT-4o mini Sentiment Results
Folder: [`2f-manual-validation/`](2f-manual-validation/)

- `sampling_comment.ipynb`: Sample 354 HN GH-AI comments (excluding those already in the ground truth) stratified by story and comment sentiment, for manual validation of the GPT-4o mini output.
- `cohen_kappa_agreement.ipynb`: Compute Cohen's kappa agreement between the two human investigators and against the GPT-4o mini labels, for the sampled stories (`sampled_328_hu_gh_ai_story_2hu_labeled.csv`) and comments (`sampled_354_hn_gh_ai_comment_2hu_labeled.csv`).
- `gwen_ac1.ipynb`: Compute Gwet's AC1 agreement between the GPT-4o mini labels and the human consensus labels on the same samples.

## RQ2 Dataset Schema
Folder: [`dataset/`](dataset/)

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
