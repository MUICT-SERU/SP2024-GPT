import pandas as pd

# Load the dataset
file_path = "../../dataset/nonhn-gh-ai-metrics-[2147].csv"
df = pd.read_csv(file_path, encoding='utf-7')

# Sort data by repo and month (assuming month format is YYYY-MM-DD)
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
df = df.sort_values(by=['control_repo', 'month'])

# List of metrics to be accumulated
metrics = ['new_stars', 'new_forks', 'new_commits', 'new_prs', 'active_contributors']
cumulative_metrics = {metric: f'cumulative_{metric[4:]}' for metric in metrics}

# Initialize cumulative columns
df[list(cumulative_metrics.values())] = 0

# Compute cumulative sums per repository
df[list(cumulative_metrics.values())] = df.groupby('control_repo')[metrics].cumsum().values

# Save the updated dataframe to a new CSV file
output_file = "../../dataset/nonhn-gh-ai-metrics-cumulative.csv"
df.to_csv(output_file, index=False)

print(f"Cumulative metrics saved to {output_file}")
