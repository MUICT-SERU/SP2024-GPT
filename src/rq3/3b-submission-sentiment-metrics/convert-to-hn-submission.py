import pandas as pd
from datetime import datetime, timedelta

def process_metrics(hn_data_path, metrics_path, output_path):
    """
    Process metrics from the new format and generate output in the required format.

    Args:
        hn_data_path (str): Path to HackerNews submission data CSV
        metrics_path (str): Path to the combined metrics CSV file
        output_path (str): Path for output CSV file
    """
    # Load data
    hn_data = pd.read_csv(hn_data_path)
    metrics_data = pd.read_csv(metrics_path)

    # Convert submission date to datetime
    hn_data['date'] = pd.to_datetime(hn_data['timestamp']).dt.tz_localize(None)
    metrics_data['month'] = pd.to_datetime(metrics_data['month'], format='%Y-%m')

    # Initialize result DataFrame
    result_df = hn_data.copy()

    # metric_cols = ['cumulative_stars', 'commit_count', 'new_prs', 'cumulative_forks', 'active_contributors']
    metric_cols = ['new_stars', 'commit_count', 'new_prs', 'new_forks', 'active_contributors']
    metric_rename = {
        'new_stars': 'stars',
        'commit_count': 'commits',
        'new_prs': 'pull_requests',
        'new_forks': 'forks',
        'active_contributors': 'contributors'
    }

    # Process each repository
    for idx, row in result_df.iterrows():
        repo_url = row['url']
        submission_date = row['date']
        repo_metrics = metrics_data[metrics_data['repo_url'] == repo_url]

        # Process each metric
        for metric in metric_cols:
            metric_name = metric_rename[metric]

            # Get metric at submission date
            closest_submit_metric = repo_metrics.loc[(repo_metrics['month'] - submission_date).abs().idxmin(), metric]
            result_df.at[idx, f'{metric_name}_at_submission'] = closest_submit_metric

            # Get metric for each of the next 5 months
            for month in range(1, 6):
                target_date = submission_date + timedelta(days=30 * month)
                closest_metric = repo_metrics.loc[(repo_metrics['month'] - target_date).abs().idxmin(), metric]
                result_df.at[idx, f'{metric_name}_month_{month}'] = closest_metric

    # Save the result
    result_df.to_csv(output_path, index=False)
    print(f"Saved consolidated metrics to {output_path}")

    # Print sample of the output
    print("\nFirst few rows of the output:")
    print(result_df.head())

hn_data_path = './hn-stories-gh-ai.csv'
metrics_path = './hn-stories-gh-ai-metrics.csv'
output_path = './hn-stories-gh-ai-metrics-5months-v2-[monthly-new].csv'
process_metrics(hn_data_path, metrics_path, output_path)