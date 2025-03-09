import pandas as pd
from datetime import datetime, timedelta
import os

def load_metrics(metrics_dir):
    """
    Load all metric CSVs into a dictionary of DataFrames.

    Args:
        metrics_dir (str): Directory containing metric CSV files

    Returns:
        dict: Dictionary with metric names as keys and DataFrames as values
    """
    metrics = {}
    metric_files = ['stars', 'commits', 'pull_requests', 'forks', 'contributors']

    for metric in metric_files:
        file_path = os.path.join(metrics_dir, f'combined_{metric}_metrics.csv')
        if os.path.exists(file_path):
            metrics[metric] = pd.read_csv(file_path, index_col=0)
        else:
            print(f"Warning: {metric}_metrics.csv not found")

    return metrics

def unix_to_datetime(unix_timestamp):
    """Convert Unix timestamp to datetime object."""
    return datetime.fromtimestamp(int(unix_timestamp))

def find_closest_date_column(df, target_date):
    """
    Find the closest date column in the metrics DataFrame to the target date.

    Args:
        df (pd.DataFrame): Metrics DataFrame
        target_date (datetime): Target date to match

    Returns:
        str: Name of the closest date column
    """
    # Convert column names to datetime objects
    date_cols = [datetime.strptime(col, '%Y-%m') for col in df.columns]

    # Find the column with the minimum absolute difference
    closest_date = min(date_cols, key=lambda x: abs(x - target_date))

    # Convert back to original format
    return closest_date.strftime('%Y-%m')

def get_metric_value(df, repo_url, date_col):
    """
    Get metric value for a specific repository and date.
    Returns -1 if data is not available.
    """
    try:
        return df.loc[repo_url, date_col]
    except:
        return -1

def process_metrics(hn_data_path, metrics_dir, output_path):
    """
    Process metrics and create consolidated CSV file.

    Args:
        hn_data_path (str): Path to HackerNews submission data CSV
        metrics_dir (str): Directory containing metric CSVs
        output_path (str): Path for output CSV file
    """
    # Load HackerNews submission data
    hn_data = pd.read_csv(hn_data_path)

    # Load all metrics
    metrics_dict = load_metrics(metrics_dir)
    if not metrics_dict:
        raise ValueError("No metric files found")

    # Initialize result DataFrame with HackerNews metadata
    result_df = hn_data.copy()

    # Process each repository
    for idx, row in result_df.iterrows():
        repo_url = row['url']
        submission_date = unix_to_datetime(row['date'])

        # Process each metric type
        for metric_name, metric_df in metrics_dict.items():
            # Get metrics at submission date
            closest_submit_date = find_closest_date_column(metric_df, submission_date)
            result_df.at[idx, f'{metric_name}_at_submission'] = get_metric_value(
                metric_df, repo_url, closest_submit_date)

            # Get metrics for each month after submission
            for month in range(1, 6):
                target_date = submission_date + timedelta(days=30 * month)
                closest_month_date = find_closest_date_column(metric_df, target_date)
                result_df.at[idx, f'{metric_name}_month_{month}'] = get_metric_value(
                    metric_df, repo_url, closest_month_date)

    # Save the result
    result_df.to_csv(output_path, index=False)
    print(f"Saved consolidated metrics to {output_path}")

    # Print sample of the output
    print("\nFirst few rows of the output:")
    print(result_df.head())

# Update these paths according to your file structure
HN_DATA_PATH = "/content/drive/MyDrive/datasets/muict-naist-senior/rq1/rq1_freq_analysis/rq1_stories_github.csv"
METRICS_DIR = "./"
OUTPUT_PATH = "consolidated_metrics.csv"

process_metrics(HN_DATA_PATH, METRICS_DIR, OUTPUT_PATH)