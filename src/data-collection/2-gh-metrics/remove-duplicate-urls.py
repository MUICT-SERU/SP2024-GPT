import pandas as pd

def remove_duplicate_urls(input_path, output_path):
    """
    Remove rows with duplicated 'url' values, keeping only one with the highest HN story scores.

    Args:
        input_path (str): Path to the input CSV file.
        output_path (str): Path to save the cleaned CSV file.
    """
    # Load the CSV file
    df = pd.read_csv(input_path)

    # Drop duplicate URLs, keeping the first occurrence with the highest HN story score
    df_cleaned = df.sort_values('score', ascending=False).drop_duplicates(subset=['url'], keep='first')

    # Save the cleaned DataFrame
    df_cleaned.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path}")

csv_input = './hn-stories-gh-ai-metrics.csv'
csv_output = './hn-stories-gh-ai-metrics-[no-duplicates].csv'
remove_duplicate_urls(csv_input, csv_output)