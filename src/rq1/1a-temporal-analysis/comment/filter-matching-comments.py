import pandas as pd
import csv

def filter_comments_by_story_ids():
    # Load the story CSV to get valid story IDs
    stories_df = pd.read_csv('./hn-stories-ai.csv')
    valid_story_ids = set(stories_df['id'].astype(str))

    # Load the comments CSV and filter
    comments_df = pd.read_csv('./hn-comments-all.csv')
    filtered_comments = comments_df[comments_df['story_id'].astype(str).isin(valid_story_ids)]

    # Save the filtered comments
    filtered_comments.to_csv('hn-comments-ai.csv', index=False)

    print(f"Original comments count: {len(comments_df)}")
    print(f"Filtered comments count: {len(filtered_comments)}")
    print(f"Removed {len(comments_df) - len(filtered_comments)} comments")

if __name__ == "__main__":
    filter_comments_by_story_ids()