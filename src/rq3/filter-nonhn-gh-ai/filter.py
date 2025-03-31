import pandas as pd

# Keywords to search for (only in the repo name part, after the slash)
keywords = [
    'artificial-intelligence',
    '-ai-',
    'natural-language-processing',
    '-nlp-',
    'language-model',
    '-llm-',
    'chatbot',
    'chatgpt',
    'openai',
    'claude',
    '-llama-',
    '-gpt-',
    'neural'
]

def repo_contains_keyword(control_repo):
    if not isinstance(control_repo, str):  # Skip NaN/None values
        return False

    # Split into owner and repo name (take the part after the last slash)
    parts = control_repo.split('/')
    if len(parts) < 2:  # No slash? Skip.
        return False

    repo_name = parts[-1].lower()  # Get repo name (after last slash) and lowercase it

    # Check if any keyword is in the repo name (not owner name)
    return any(keyword in repo_name for keyword in keywords)

# Read the CSV file
file_path = 'nonhn-gh-ai-metrics-[2500].csv'
try:
    df = pd.read_csv(file_path)

    if 'control_repo' not in df.columns:
        print("Error: 'control_repo' column not found in the CSV file.")
    else:
        # Apply filtering (only where repo name contains keywords)
        filtered_df = df[df['control_repo'].apply(repo_contains_keyword)]

        # Save filtered data
        output_file = 'filtered_nonhn-gh-ai-metrics.csv'
        filtered_df.to_csv(output_file, index=False)
        print(f"Filtered data saved to {output_file}")
        print(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")

except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
except Exception as e:
    print(f"An error occurred: {str(e)}")