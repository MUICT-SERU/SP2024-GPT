import csv
import requests
import time
import os
import pandas as pd
from urllib.parse import urlparse

# GitHub API token (set as an environment variable or replace with your token)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Input CSV file
INPUT_CSV = "./hn-stories-gh-ai-[no-dupes].csv"
OUTPUT_CSV = "hn-stories-gh-ai-metadata.csv"

def extract_repo_owner_and_name(repo_url):
    """Extracts owner and repo name from a GitHub URL."""
    path_parts = urlparse(repo_url).path.strip("/").split("/")
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    return None, None

def get_github_metadata(repo_url):
    """Fetches GitHub metadata for a given repository."""
    owner, repo = extract_repo_owner_and_name(repo_url)
    if not owner or not repo:
        return None

    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(api_url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return {
            "repo_name": data.get("full_name"),
            "created_at": data.get("created_at"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "watchers": data.get("watchers_count"),
            "language": data.get("language"),
            # "license": data.get("license", {}).get("name"),
        }
    else:
        print(f"Failed to retrieve {repo_url}, status code: {response.status_code}")
        return None

def process_csv(input_csv, output_csv):
    """Reads input CSV, retrieves metadata, and saves to output CSV."""
    df = pd.read_csv(input_csv)

    metadata_list = []
    for index, row in df.iterrows():
        repo_url = row.get("url")
        if isinstance(repo_url, str) and "github.com" in repo_url:
            metadata = get_github_metadata(repo_url)
            if metadata:
                metadata_list.append(metadata)
            else:
                metadata_list.append({"repo_name": None, "created_at": None, "stars": None, "forks": None, "watchers": None, "language": None, "license": None})
        else:
            metadata_list.append({"repo_name": None, "created_at": None, "stars": None, "forks": None, "watchers": None, "language": None, "license": None})
        time.sleep(1)  # Avoid hitting rate limits

    metadata_df = pd.DataFrame(metadata_list)
    result_df = pd.concat([df, metadata_df], axis=1)
    result_df.to_csv(output_csv, index=False)

if __name__ == "__main__":
    process_csv(INPUT_CSV, OUTPUT_CSV)
    print(f"Metadata saved to {OUTPUT_CSV}")
