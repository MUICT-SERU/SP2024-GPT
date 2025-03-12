import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Load datasets
# 1. Treatment repos with HackerNews submission dates
treatment_df = pd.read_csv('hn-gh-ai-metrics-[6months-before-after-hn].csv')
# 2. Potential control repos (full metrics file)
control_candidates_df = pd.read_csv('./nonhn-gh-ai-metrics-v3-[2500].csv')

# Convert date columns to datetime
treatment_df['month'] = pd.to_datetime(treatment_df['month'])
treatment_df['hn_submission_date'] = pd.to_datetime(treatment_df['hn_submission_date'])
control_candidates_df['month'] = pd.to_datetime(control_candidates_df['month'])

# Function to find the closest month data for a given date
def find_closest_month_data(df, repo_name, target_date):
    """Find the data row closest to the target date for a specific repo"""
    repo_data = df[df['repo_full_name'] == repo_name]

    if repo_data.empty:
        return None

    # Calculate absolute difference between each month and target date
    repo_data = repo_data.copy()
    repo_data['date_diff'] = abs(repo_data['month'] - target_date)

    # Get the row with minimum difference
    closest_row = repo_data.loc[repo_data['date_diff'].idxmin()]
    closest_row = closest_row.drop('date_diff')

    return closest_row

# Extract unique treatment repos with their HN submission dates
treatment_repos = treatment_df[['repo_full_name', 'hn_submission_date']].drop_duplicates()

# Get unique control repos
control_repos = control_candidates_df['repo_full_name'].unique()

# For each treatment repo, find the best matching control repo
matches = []

i = 0
for _, treatment_row in treatment_repos.iterrows():
    i += 1
    print(i,'out of',len(treatment_repos))
    treatment_repo = treatment_row['repo_full_name']
    hn_date = treatment_row['hn_submission_date']

    # Find the month closest to the HN submission date for the treatment repo
    treatment_data = find_closest_month_data(treatment_df, treatment_repo, hn_date)

    if treatment_data is None:
        continue

    # Define metrics to match on
    match_metrics = ['cumulative_stars', 'cumulative_forks', 'commit_count', 'active_contributors']

    best_match = None
    best_score = float('inf')

    # For each potential control repo, calculate similarity score
    for control_repo in control_repos:
        # Skip if the control repo is the same as the treatment repo
        if control_repo == treatment_repo:
            continue

        # Get control repo data closest to the HN submission date
        control_data = find_closest_month_data(control_candidates_df, control_repo, hn_date)

        if control_data is None:
            continue

        # Calculate similarity score based on the metrics
        score = 0
        for metric in match_metrics:
            if metric in treatment_data and metric in control_data:
                # Calculate normalized absolute difference
                t_value = treatment_data[metric]
                c_value = control_data[metric]

                # Avoid division by zero - if both are zero, they're perfectly matched on this metric
                if t_value == 0 and c_value == 0:
                    metric_score = 0
                elif t_value == 0 or c_value == 0:
                    metric_score = 1  # Maximum difference if one is zero and other isn't
                else:
                    # Logarithmic distance for values that can vary by orders of magnitude
                    log_t = np.log1p(t_value) if t_value > 0 else 0
                    log_c = np.log1p(c_value) if c_value > 0 else 0
                    metric_score = abs(log_t - log_c)

                score += metric_score

        # If this control repo has a better score, update the best match
        if score < best_score:
            best_score = score
            best_match = {
                'treatment_repo': treatment_repo,
                'treatment_repo_url': f"https://github.com/{treatment_repo}",
                'hn_submission_date': hn_date,
                'treatment_stars': treatment_data['cumulative_stars'],
                'treatment_forks': treatment_data['cumulative_forks'],
                'control_repo': control_repo,
                'control_stars': control_data['cumulative_stars'],
                'control_forks': control_data['cumulative_forks'],
                'similarity_score': score,
                'commit_difference': abs(treatment_data['commit_count'] - control_data['commit_count']),
                'contrib_difference': abs(treatment_data['active_contributors'] - control_data['active_contributors'])
            }

    if best_match:
        matches.append(best_match)

# Create DataFrame from matches and sort by similarity score
matches_df = pd.DataFrame(matches)
matches_df = matches_df.sort_values('similarity_score')

# Save to CSV
matches_df.to_csv('improved_treatment_control_pairs.csv', index=False)

print(f"Created {len(matches_df)} treatment-control pairs.")
print("Pairs sorted from best match (lowest score) to worst match.")
print("\nTop 5 matches:")
print(matches_df.head(5)[['treatment_repo', 'control_repo', 'similarity_score', 'treatment_stars', 'control_stars']])

# Optional: Calculate additional statistics about the matches
print("\nMatching Statistics:")
print(f"Average similarity score: {matches_df['similarity_score'].mean():.2f}")
print(f"Median similarity score: {matches_df['similarity_score'].median():.2f}")
print(f"Average star difference: {abs(matches_df['treatment_stars'] - matches_df['control_stars']).mean():.2f}")
print(f"Average fork difference: {abs(matches_df['treatment_forks'] - matches_df['control_forks']).mean():.2f}")

# Create a histogram of similarity scores
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.hist(matches_df['similarity_score'], bins=20, edgecolor='black')
plt.title('Distribution of Similarity Scores')
plt.xlabel('Similarity Score (lower is better)')
plt.ylabel('Number of Pairs')
plt.grid(True, alpha=0.3)
plt.show()