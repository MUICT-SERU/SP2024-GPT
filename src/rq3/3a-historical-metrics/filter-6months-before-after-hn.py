import pandas as pd
from datetime import datetime, timedelta

# Load the datasets
metrics_df = pd.read_csv("hn-stories-gh-ai-metrics.csv")
metadata_df = pd.read_csv("hn-stories-gh-ai-metadata.csv")

# Convert date columns to datetime objects
metrics_df['month'] = pd.to_datetime(metrics_df['month']).dt.tz_localize(None)
metrics_df['hn_submission_date'] = pd.to_datetime(metrics_df['hn_submission_date']).dt.tz_localize(None)
metadata_df['repo_creation_date'] = pd.to_datetime(metadata_df['repo_creation_date']).dt.tz_localize(None)

# Define cutoff date for second criterion
submission_cutoff = pd.to_datetime('2024-06-01')

# Create a dictionary to store the earliest submission date for each repo
earliest_submissions = {}
for repo, group in metrics_df.groupby('repo_full_name'):
    earliest_submissions[repo] = group['hn_submission_date'].min()

# Function to check if a repo meets the criteria
def meets_criteria(repo_name):
    if repo_name not in earliest_submissions:
        return False

    # Get the earliest HN submission date for this repo
    submission_date = earliest_submissions[repo_name]

    # Criterion 2: Check if HN submission is before June 2024
    if submission_date >= submission_cutoff:
        return False

    # Check if repo exists in metadata
    if repo_name not in metadata_df['repo_full_name'].values:
        return False

    # Get repo creation date
    creation_date = metadata_df.loc[metadata_df['repo_full_name'] == repo_name, 'repo_creation_date'].iloc[0]

    # Criterion 1: Check if repo was created at least 6 months before HN submission
    six_months = timedelta(days=180)  # Approximating 6 months as 180 days
    if creation_date > (submission_date - six_months):
        return False

    return True

# Filter repos that meet the criteria
qualified_repos = [repo for repo in earliest_submissions.keys() if meets_criteria(repo)]

# Create filtered dataframes
filtered_metrics = metrics_df[metrics_df['repo_full_name'].isin(qualified_repos)]
filtered_metadata = metadata_df[metadata_df['repo_full_name'].isin(qualified_repos)]

# Save filtered data to new CSV files
filtered_metrics.to_csv("filtered_metrics_for_did.csv", index=False)
filtered_metadata.to_csv("filtered_metadata_for_did.csv", index=False)

# Print summary statistics
print(f"Total repositories: {len(earliest_submissions)}")
print(f"Qualified repositories: {len(qualified_repos)}")
print(f"Percentage qualified: {len(qualified_repos)/len(earliest_submissions)*100:.2f}%")

# Print first few qualified repos for verification
print("\nSample of qualified repositories:")
for repo in qualified_repos[:5]:
    creation_date = metadata_df.loc[metadata_df['repo_full_name'] == repo, 'repo_creation_date'].iloc[0]
    submission_date = earliest_submissions[repo]
    months_before = (submission_date - creation_date).days / 30  # approximate months

    # Count months after submission
    repo_data = metrics_df[metrics_df['repo_full_name'] == repo]
    post_submission_months = repo_data[repo_data['month'] >= submission_date]['month'].nunique()

    print(f"{repo}: Created {months_before:.1f} months before HN submission, has {post_submission_months} months of data after")