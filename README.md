# Social Media Reactions to Open Source Projects: A Study on AI projects on HackerNews

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
