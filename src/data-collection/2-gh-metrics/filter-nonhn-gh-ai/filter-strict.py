import pandas as pd
import re

# Keywords to search for (strict whole-word matching)
keywords = [
    'artificial intelligence',
    'ai',
    'natural language processing',
    'nlp',
    'language model',
    'llm',
    'chatbot',
    'chatgpt',
    'openai',
    'claude',
    'llama',
    'gpt',
    'neural'
]

def repo_contains_keyword(repo_full_name):
    if not isinstance(repo_full_name, str):  # Skip NaN/None
        return False

    parts = repo_full_name.split('/')
    if len(parts) < 2:  # No slash? Skip.
        return False

    repo_name = parts[-1].lower()  # Repo name only (lowercase)

    for keyword in keywords:
        # Replace spaces with any separator (-, _, or space)
        keyword_pattern = re.escape(keyword.lower()).replace(r'\ ', r'[ _-]')

        # Regex: Word boundaries + keyword (with optional separators between words)
        pattern = re.compile(
            r'\b' + keyword_pattern + r'\b',
            flags=re.IGNORECASE
        )
        if pattern.search(repo_name):
            return True

    return False

# Read CSV
file_path = 'nonhn-gh-ai-metadata.csv'
try:
    df = pd.read_csv(file_path)

    if 'repo_full_name' not in df.columns:
        print("Error: 'repo_full_name' column not found.")
    else:
        filtered_df = df[df['repo_full_name'].apply(repo_contains_keyword)]

        # Save results
        output_file = 'filtered_nonhn-gh-ai-metadata-strict.csv'
        filtered_df.to_csv(output_file, index=False)
        print(f"Filtered data saved to {output_file}")
        print(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")

except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
except Exception as e:
    print(f"An error occurred: {str(e)}")