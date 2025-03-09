import pandas as pd
import os
import glob

# List of metrics
metrics = ["commits", "contributors", "forks", "pull_requests", "stars"]

# Loop through each metric
for metric in metrics:
    # Get all CSV files for the current metric
    csv_files = sorted(glob.glob(f"*_{metric}_metrics.csv"))

    # Read and concatenate all CSV files for this metric
    df_list = [pd.read_csv(file, index_col=0) for file in csv_files]
    combined_df = pd.concat(df_list)

    # Drop duplicates if any (keeping the first occurrence)
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]

    # Save the combined CSV
    # create directory if it doesn't exist
    if not os.path.exists("./output"):
        os.makedirs("./output")
    combined_df.to_csv(f"./output/{metric}_combined.csv")
    print(f"Saved {metric}_combined.csv")