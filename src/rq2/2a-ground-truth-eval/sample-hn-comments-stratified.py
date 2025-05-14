import pandas as pd
import numpy as np

HN_COMMENTS_CSV = '../../rq1/dataset/hn-comments-gh-ai.csv'
HN_COMMENTS_SAMPLED_CSV = '../dataset/hn-comments-gh-ai-sampled.csv'

def stratified_sample_with_min_per_story(csv_file, num_samples, output_file):
    df = pd.read_csv(csv_file)

    # Drop duplicates based on both 'comment_id' and 'comment_text'
    df = df.drop_duplicates(subset=['comment_id', 'comment_text'])

    # Group by 'story_id' (which represents each story)
    grouped = df.groupby('story_id')

    # Initialize an empty DataFrame to store the sampled data
    sampled_df = pd.DataFrame()

    # Step 1: Ensure each story gets at least one comment
    for name, group in grouped:
        if len(group) > 1:
            sampled_df = pd.concat([sampled_df, group.sample(n=1, random_state=42)])
        else:
            sampled_df = pd.concat([sampled_df, group])

    # Step 2: Calculate the remaining number of comments to sample
    remaining_samples = num_samples - len(sampled_df)

    if remaining_samples > 0:
        # Step 3: Sample the remaining comments proportionally to the size of each group
        proportion = remaining_samples / (len(df) - len(sampled_df))

        # Remove the previously sampled data from the original dataframe to avoid duplicates
        df_remaining = df[~df.index.isin(sampled_df.index)]

        # Sample remaining comments proportionally
        remaining_sampled = df_remaining.groupby('story_id', group_keys=False).apply(
            lambda x: x.sample(frac=proportion, random_state=42) if len(x) > 1 else pd.DataFrame()
        )

        # Combine the guaranteed 1 comment samples with the remaining proportional samples
        sampled_df = pd.concat([sampled_df, remaining_sampled])

    # Ensure the final number of samples matches exactly num_samples
    if len(sampled_df) > num_samples:
        sampled_df = sampled_df.sample(n=num_samples, random_state=42)

    # Save the sampled data to a new CSV file
    sampled_df.to_csv(output_file, index=False)

stratified_sample_with_min_per_story(HN_COMMENTS_CSV, 385, HN_COMMENTS_SAMPLED_CSV)


def get_comment_statistics(csv_file):
    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Group by 'story_id' and count the number of comments in each story
    comment_counts = df.groupby('story_id').size().reset_index(name='num_comments')

    # Calculate overall statistics
    total_stories = comment_counts['story_id'].nunique()
    total_comments = comment_counts['num_comments'].sum()
    max_comments = comment_counts['num_comments'].max()
    min_comments = comment_counts['num_comments'].min()
    avg_comments = comment_counts['num_comments'].mean()

    # Print the statistics
    print(f"Total number of stories: {total_stories}")
    print(f"Total number of comments: {total_comments}")
    print(f"Average number of comments per story: {avg_comments:.2f}")
    print(f"Max number of comments in a story: {max_comments}")
    print(f"Min number of comments in a story: {min_comments}")

    # Return the DataFrame containing the number of comments per story
    return comment_counts

comment_stats = get_comment_statistics(HN_COMMENTS_CSV)
print(comment_stats)