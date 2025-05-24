import pandas as pd
import numpy as np

HN_STORIES_CSV = '../../rq1/dataset/hn-stories-gh-ai.csv'
HN_COMMENTS_CSV = '../../rq1/dataset/hn-comments-gh-ai.csv'

SAMPLED_STORIES_CSV = '../dataset/hn-stories-gh-ai-sampled.csv'
SAMPLED_COMMENTS_CSV = '../dataset/hn-comments-gh-ai-sampled.csv'

NUM_STORIES = 385
NUM_COMMENTS = 385

def sample_uniform_stories(stories_csv, num_stories, output_file):
    stories_df = pd.read_csv(stories_csv)
    sampled_stories_df = stories_df.sample(n=num_stories, random_state=42)
    sampled_stories_df.to_csv(output_file, index=False)
    print(f"✅ Sampled {len(sampled_stories_df)} stories saved to {output_file}")
    return sampled_stories_df


def sample_stratified_comments_with_fallback(sampled_stories_df, comments_csv, num_comments, output_file):
    comments_df = pd.read_csv(comments_csv)
    sampled_story_ids = set(sampled_stories_df['id'])

    # Filter comments from sampled stories
    filtered_comments = comments_df[comments_df['story_id'].isin(sampled_story_ids)]

    # Group by story_id
    grouped = filtered_comments.groupby('story_id', group_keys=False)
    group_sizes = grouped.size()

    # Proportional allocation
    proportions = (group_sizes / group_sizes.sum()) * num_comments
    samples_per_group = proportions.round().astype(int)

    # Adjust to exactly num_comments
    while samples_per_group.sum() != num_comments:
        diff = num_comments - samples_per_group.sum()
        adjust_idx = samples_per_group.sample(n=1, random_state=42).index[0]
        samples_per_group[adjust_idx] += np.sign(diff)

    # Stratified sampling
    def sample_group(g):
        count = samples_per_group.get(g.name, 0)
        return g.sample(n=min(len(g), count), random_state=42)

    stratified_sample = grouped.apply(sample_group)

    # Fill missing by sampling 1 comment per new random story
    if len(stratified_sample) < num_comments:
        already_sampled_ids = set(stratified_sample['comment_id'])
        already_sampled_story_ids = set(stratified_sample['story_id'])

        # Get stories with unsampled comments
        remaining_comments = filtered_comments[~filtered_comments['comment_id'].isin(already_sampled_ids)]
        remaining_story_groups = remaining_comments.groupby('story_id')

        # Remove stories we've already exhausted
        candidate_stories = [story_id for story_id in remaining_story_groups.groups.keys()
                             if story_id not in already_sampled_story_ids]

        np.random.seed(42)
        np.random.shuffle(candidate_stories)

        extra_samples = []

        for story_id in candidate_stories:
            group = remaining_story_groups.get_group(story_id)
            print(f"Sampling from story_id {story_id} with {len(group)} comments")
            if not group.empty:
                extra_samples.append(group.sample(n=1, random_state=42))
            if len(extra_samples) + len(stratified_sample) >= num_comments:
                break

        # If still under, allow reuse from already sampled stories
        if len(extra_samples) + len(stratified_sample) < num_comments:
            additional_needed = num_comments - (len(extra_samples) + len(stratified_sample))
            reuse_comments = remaining_comments.sample(n=additional_needed, random_state=42)
            extra_samples.append(reuse_comments)

        extra_sample_df = pd.concat(extra_samples)

        final_sample = pd.concat([stratified_sample, extra_sample_df])
    else:
        final_sample = stratified_sample


    # Merge with story metadata
    final_sample = final_sample.merge(
        sampled_stories_df,
        how='left',
        left_on='story_id',
        right_on='id',
        suffixes=('_comment', '_story')
    )

    final_sample.to_csv(output_file, index=False)
    print(f"✅ Sampled {len(final_sample)} comments saved to {output_file}")
    return final_sample


# Run sampling
sampled_stories_df = sample_uniform_stories(HN_STORIES_CSV, NUM_STORIES, SAMPLED_STORIES_CSV)
sampled_comments_df = sample_stratified_comments_with_fallback(sampled_stories_df, HN_COMMENTS_CSV, NUM_COMMENTS, SAMPLED_COMMENTS_CSV)
