import pandas as pd
from tqdm import tqdm

"""_summary_
Filter comments that contains story IDs in the specified stories csv.
"""

def filter_comments_by_story_ids():
    # Load the story CSV to get valid story IDs
    stories_csv_path = './hn-stories-gh-ai.csv'
    stories_df = pd.read_csv(stories_csv_path, sep=',')
    valid_story_ids = set(stories_df['id'].astype(str))

    # Load the comments CSV and filter in chunks
    comments_csv_path = './hn-comments-all.csv'
    filtered_comments = []

    for chunk in tqdm(pd.read_csv(comments_csv_path, sep=',', chunksize=2000)):
        chunk_filtered = chunk[chunk['story_id'].astype(str).isin(valid_story_ids)]
        filtered_comments.append(chunk_filtered)

    # Concatenate all filtered chunks
    filtered_comments_df = pd.concat(filtered_comments)

    # Save the filtered comments
    filtered_comments_df.to_csv('hn-comments-gh-ai.csv', index=False)

    print(f"Filtered comments count: {len(filtered_comments_df)}")

if __name__ == "__main__":
    filter_comments_by_story_ids()