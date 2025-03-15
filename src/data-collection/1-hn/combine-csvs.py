
import pandas as pd

# Read the two CSV files
df1 = pd.read_csv('./hn-stories-gh-[new-only]-[distinct-urls].csv')
df2 = pd.read_csv('file2.csv')

# Combine the dataframes

combined_df = pd.concat([df1, df2], ignore_index=True)

# Export to a new CSV file
combined_df.to_csv('combined_output.csv', index=False)
