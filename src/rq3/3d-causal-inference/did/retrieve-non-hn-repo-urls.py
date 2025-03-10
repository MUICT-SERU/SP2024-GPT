import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime, timedelta

# Load the datasets
metrics_df = pd.read_csv("hn-stories-gh-ai-metrics.csv")
metadata_df = pd.read_csv("hn-stories-gh-ai-metadata.csv")
filtered_metrics = pd.read_csv("filtered_metrics_for_did.csv")  # Treatment repos we filtered earlier

# Convert date columns to datetime
metrics_df['month'] = pd.to_datetime(metrics_df['month']).dt.tz_localize(None)
metrics_df['hn_submission_date'] = pd.to_datetime(metrics_df['hn_submission_date']).dt.tz_localize(None)
metadata_df['repo_creation_date'] = pd.to_datetime(metadata_df['repo_creation_date']).dt.tz_localize(None)
filtered_metrics['month'] = pd.to_datetime(filtered_metrics['month']).dt.tz_localize(None)
filtered_metrics['hn_submission_date'] = pd.to_datetime(filtered_metrics['hn_submission_date']).dt.tz_localize(None)

# Get list of treatment repos (from our filtered dataset)
treatment_repos = filtered_metrics['repo_full_name'].unique()

# Find all AI-related repos that were never submitted to HackerNews (potential controls)
all_repos = metrics_df['repo_full_name'].unique()
potential_control_repos = [repo for repo in all_repos if repo not in treatment_repos]

print(f"Treatment repos: {len(treatment_repos)}")
print(f"Potential control repos: {len(potential_control_repos)}")

# Create a dictionary to store treatment repos' submission dates and metrics at submission
treatment_info = {}
for repo in treatment_repos:
    repo_data = filtered_metrics[filtered_metrics['repo_full_name'] == repo]
    submission_date = repo_data['hn_submission_date'].iloc[0]

    # Find the metrics at (or closest to) the submission date
    closest_month = repo_data.iloc[np.abs(repo_data['month'] - submission_date).argsort()[:1]]

    # Extract metrics at submission time
    stars = closest_month['cumulative_stars'].iloc[0]
    forks = closest_month['cumulative_forks'].iloc[0]

    # Get creation date from metadata
    creation_date = metadata_df.loc[metadata_df['repo_full_name'] == repo, 'repo_creation_date'].iloc[0] \
        if repo in metadata_df['repo_full_name'].values else None

    treatment_info[repo] = {
        'submission_date': submission_date,
        'creation_date': creation_date,
        'stars': stars,
        'forks': forks
    }

# For each potential control repo, get metrics for all months
control_metrics = {}
for repo in potential_control_repos:
    repo_data = metrics_df[metrics_df['repo_full_name'] == repo]

    # Only include if repo has sufficient data
    if len(repo_data) < 6:  # At least 6 months of data
        continue

    # Get creation date from metadata
    creation_date = metadata_df.loc[metadata_df['repo_full_name'] == repo, 'repo_creation_date'].iloc[0] \
        if repo in metadata_df['repo_full_name'].values else None

    if creation_date is None:
        continue

    # Store metrics by month
    monthly_metrics = {}
    for _, row in repo_data.iterrows():
        month = row['month']
        monthly_metrics[month] = {
            'stars': row['cumulative_stars'],
            'forks': row['cumulative_forks']
        }

    control_metrics[repo] = {
        'creation_date': creation_date,
        'monthly_metrics': monthly_metrics
    }

print(f"Control repos with sufficient data: {len(control_metrics)}")

# Function to find the best matching control repo for a treatment repo
def find_matching_control(treatment_repo, treatment_data, controls, k=5):
    submission_date = treatment_data['submission_date']
    creation_date = treatment_data['creation_date']
    target_stars = treatment_data['stars']
    target_forks = treatment_data['forks']

    candidates = []

    for control_repo, control_data in tqdm(controls.items(), desc=f"Matching {treatment_repo}"):
        # Skip if creation date is too different (±3 months)
        control_creation = control_data['creation_date']
        creation_diff = abs((creation_date - control_creation).days)
        if creation_diff > 90:  # Approximately 3 months
            continue

        # Find metrics closest to the treatment's submission date
        best_month = None
        smallest_diff = float('inf')

        for month in control_data['monthly_metrics'].keys():
            # Only consider months after control was created + 6 months (to match filter criteria)
            if month < control_creation + timedelta(days=180):
                continue

            # Only use months before June 2024 (to match filter criteria)
            if month >= pd.to_datetime('2024-06-01'):
                continue

            diff = abs((month - submission_date).days)
            if diff < smallest_diff:
                smallest_diff = diff
                best_month = month

        if best_month is None:
            continue

        # Get metrics at the best matching month
        control_stars = control_data['monthly_metrics'][best_month]['stars']
        control_forks = control_data['monthly_metrics'][best_month]['forks']

        # Calculate similarity based on stars and forks
        # We use log to handle the wide range of values
        if target_stars == 0 or control_stars == 0:
            star_diff = abs(target_stars - control_stars)
        else:
            star_diff = abs(np.log1p(target_stars) - np.log1p(control_stars))

        if target_forks == 0 or control_forks == 0:
            fork_diff = abs(target_forks - control_forks)
        else:
            fork_diff = abs(np.log1p(target_forks) - np.log1p(control_forks))

        # Combined distance metric
        distance = np.sqrt(star_diff**2 + fork_diff**2)

        candidates.append({
            'control_repo': control_repo,
            'distance': distance,
            'matched_month': best_month,
            'control_stars': control_stars,
            'control_forks': control_forks,
            'star_diff': abs(target_stars - control_stars),
            'fork_diff': abs(target_forks - control_forks)
        })

    # Sort by similarity (lower distance is better)
    candidates.sort(key=lambda x: x['distance'])

    # Return top k matches
    return candidates[:k]

# Match each treatment repo to control repos
matched_controls = {}
for repo, data in treatment_info.items():
    matches = find_matching_control(repo, data, control_metrics)
    if matches:
        matched_controls[repo] = matches

# Create a dataframe with the matching results
results = []
for treatment_repo, matches in matched_controls.items():
    treatment_data = treatment_info[treatment_repo]

    for i, match in enumerate(matches):
        control_repo = match['control_repo']
        results.append({
            'treatment_repo': treatment_repo,
            'control_repo': control_repo,
            'rank': i + 1,
            'distance': match['distance'],
            'treatment_submission_date': treatment_data['submission_date'],
            'control_matched_month': match['matched_month'],
            'treatment_stars': treatment_data['stars'],
            'control_stars': match['control_stars'],
            'star_diff': match['star_diff'],
            'treatment_forks': treatment_data['forks'],
            'control_forks': match['control_forks'],
            'fork_diff': match['fork_diff'],
            'treatment_creation_date': treatment_data['creation_date'],
            'control_creation_date': control_metrics[control_repo]['creation_date'],
        })

matching_df = pd.DataFrame(results)

# Save the matching results
matching_df.to_csv("treatment_control_matches.csv", index=False)

# Print summary statistics
print(f"\nSuccessfully matched {len(matched_controls)} treatment repos to control repos")
print(f"Average number of matches per treatment: {len(matching_df) / len(matched_controls):.2f}")

# Calculate average metrics differences for top matches (rank=1)
top_matches = matching_df[matching_df['rank'] == 1]
avg_star_diff_pct = top_matches['star_diff'].mean() / top_matches['treatment_stars'].replace(0, 1).mean() * 100
avg_fork_diff_pct = top_matches['fork_diff'].mean() / top_matches['treatment_forks'].replace(0, 1).mean() * 100

print(f"\nFor top matches:")
print(f"Average absolute star difference: {top_matches['star_diff'].mean():.2f}")
print(f"Average absolute fork difference: {top_matches['fork_diff'].mean():.2f}")
print(f"Average percentage star difference: {avg_star_diff_pct:.2f}%")
print(f"Average percentage fork difference: {avg_fork_diff_pct:.2f}%")