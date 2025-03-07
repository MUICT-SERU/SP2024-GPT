import requests
import pandas as pd
import time
import numpy as np
import os
from datetime import datetime, timedelta
import random
from tqdm import tqdm

# GitHub API setup
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # Set your GitHub token as an environment variable
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_ai_repos(start_date, end_date, min_stars=10, page_count=10, repos_per_page=100):
    """
    Retrieve AI-related GitHub repositories created between start_date and end_date.

    Parameters:
    - start_date: Start date in 'YYYY-MM-DD' format
    - end_date: End date in 'YYYY-MM-DD' format
    - min_stars: Minimum stars to consider (for quality filter)
    - page_count: Number of pages to retrieve
    - repos_per_page: Repositories per page

    Returns:
    - List of repository information dictionaries
    """
    all_repos = []

    # AI-related topics and search terms
    ai_topics = ["artificial-intelligence", "machine-learning", "deep-learning", "neural-networks",
                 "ai", "ml", "nlp", "computer-vision", "reinforcement-learning", "llm"]

    # We'll search for each topic separately to get a diverse set
    for topic in tqdm(ai_topics, desc="Searching AI topics"):
        # Create a search query
        query = f"topic:{topic} created:{start_date}..{end_date} stars:>={min_stars}"

        for page in range(1, page_count + 1):
            try:
                url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={repos_per_page}&page={page}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    repos = response.json().get('items', [])
                    if not repos:
                        break  # No more results

                    all_repos.extend([{
                        'repo_url': repo['html_url'],
                        'full_name': repo['full_name'],
                        'created_at': repo['created_at'],
                        'stars': repo['stargazers_count'],
                        'forks': repo['forks_count'],
                        'language': repo['language'],
                        'description': repo['description']
                    } for repo in repos])

                elif response.status_code == 403:
                    # Rate limit exceeded
                    print("Rate limit exceeded. Waiting for 60 seconds...")
                    time.sleep(60)
                    page -= 1  # Retry this page

                else:
                    print(f"Error {response.status_code}: {response.text}")
                    break

                # Sleep to avoid hitting rate limits
                time.sleep(2)

            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                time.sleep(5)

    # Remove duplicates by repo_url
    unique_repos = list({repo['repo_url']: repo for repo in all_repos}.values())
    return unique_repos

def filter_hn_submitted_repos(all_repos, hn_submitted_repos):
    """
    Filter out repositories that were submitted to HackerNews.

    Parameters:
    - all_repos: List of repository dictionaries
    - hn_submitted_repos: List or set of HN-submitted repository URLs

    Returns:
    - Filtered list of repositories
    """
    # Convert to set for faster lookups
    hn_repos_set = set(hn_submitted_repos)

    # Filter out HN-submitted repos
    filtered_repos = [repo for repo in all_repos if repo['repo_url'] not in hn_repos_set]
    return filtered_repos

def match_control_group(treatment_repos, potential_control_repos, n_matches=1):
    """
    Match control repositories to treatment repositories based on creation date and stars.
    Uses a simple nearest-neighbor approach.

    Parameters:
    - treatment_repos: DataFrame of HN-submitted repositories
    - potential_control_repos: DataFrame of potential control repositories
    - n_matches: Number of matches per treatment repository

    Returns:
    - DataFrame of matched control repositories
    """
    # Convert dates to datetime
    treatment_repos['created_at'] = pd.to_datetime(treatment_repos['created_at'])
    potential_control_repos['created_at'] = pd.to_datetime(potential_control_repos['created_at'])

    matched_controls = []

    # Normalize stars for distance calculation
    treatment_max_stars = treatment_repos['stars'].max()
    control_max_stars = potential_control_repos['stars'].max()
    max_stars = max(treatment_max_stars, control_max_stars)

    if max_stars > 0:
        treatment_repos['stars_norm'] = treatment_repos['stars'] / max_stars
        potential_control_repos['stars_norm'] = potential_control_repos['stars'] / max_stars
    else:
        treatment_repos['stars_norm'] = treatment_repos['stars']
        potential_control_repos['stars_norm'] = potential_control_repos['stars']

    # Calculate time range for normalization
    all_dates = pd.concat([treatment_repos['created_at'], potential_control_repos['created_at']])
    min_date = all_dates.min()
    max_date = all_dates.max()
    date_range = (max_date - min_date).total_seconds()

    if date_range > 0:
        # Normalize dates to 0-1 range
        treatment_repos['date_norm'] = treatment_repos['created_at'].apply(
            lambda x: (x - min_date).total_seconds() / date_range)
        potential_control_repos['date_norm'] = potential_control_repos['created_at'].apply(
            lambda x: (x - min_date).total_seconds() / date_range)
    else:
        treatment_repos['date_norm'] = 0
        potential_control_repos['date_norm'] = 0

    # For each treatment repo, find the closest control repos
    used_control_indices = set()

    for _, treat_repo in tqdm(treatment_repos.iterrows(),
                             total=len(treatment_repos),
                             desc="Matching control repos"):
        # Calculate distance to all potential control repos
        distances = []

        for i, control_repo in potential_control_repos.iterrows():
            if i in used_control_indices:
                continue

            # Calculate Euclidean distance based on normalized date and stars
            date_diff = treat_repo['date_norm'] - control_repo['date_norm']
            stars_diff = treat_repo['stars_norm'] - control_repo['stars_norm']

            # Weight date more heavily (70%) than stars (30%)
            distance = np.sqrt((0.7 * date_diff**2) + (0.3 * stars_diff**2))
            distances.append((i, distance))

        # Sort by distance and take the closest n_matches
        sorted_distances = sorted(distances, key=lambda x: x[1])

        # Get the closest n matches (or all if fewer available)
        num_matches = min(n_matches, len(sorted_distances))
        closest_indices = [idx for idx, _ in sorted_distances[:num_matches]]

        for idx in closest_indices:
            matched_controls.append(potential_control_repos.loc[idx])
            used_control_indices.add(idx)

    return pd.DataFrame(matched_controls)

def load_hn_repo_urls(metrics_file_path):
    """
    Extract repository URLs from one of the metrics CSV files.

    Parameters:
    - metrics_file_path: Path to one of the metrics CSV files

    Returns:
    - List of repository URLs
    """
    df = pd.read_csv(metrics_file_path)
    return df['repo_url'].tolist()

def select_control_repositories(hn_repos_file,
                               start_date="2022-01-01",
                               end_date="2024-05-31",
                               min_stars=5,
                               control_ratio=2):
    """
    Main function to select control repositories for the causal inference analysis.

    Parameters:
    - hn_repos_file: Path to one of the metrics files containing HN-submitted repo URLs
    - start_date: Start date for repository creation search
    - end_date: End date for repository creation search
    - min_stars: Minimum stars for potential control repositories
    - control_ratio: Number of control repos to select per treatment repo

    Returns:
    - DataFrame of selected control repositories
    """
    # 1. Load HN-submitted repo URLs
    hn_repo_urls = load_hn_repo_urls(hn_repos_file)
    print(f"Loaded {len(hn_repo_urls)} HN-submitted repositories")

    # 2. Get potential control repositories from GitHub
    print(f"Retrieving AI repositories created between {start_date} and {end_date}")
    potential_controls = get_ai_repos(start_date, end_date, min_stars=min_stars)
    print(f"Retrieved {len(potential_controls)} potential control repositories")

    # 3. Filter out any HN-submitted repositories
    filtered_controls = filter_hn_submitted_repos(potential_controls, hn_repo_urls)
    print(f"After filtering, {len(filtered_controls)} potential control repositories remain")

    # 4. Get additional information for HN repos to enable matching
    # We're assuming we have creation dates for HN repos - if not, we'd need to fetch that
    # For this example, let's sample from the retrieved repos to simulate treatment repos
    # In your actual implementation, you'd need to get this data for your real HN repos

    # Let's simulate treatment repos by taking a sample from potential controls
    # In reality, you'd use your actual HN repo data here
    sample_size = min(300, len(potential_controls))  # Based on your ~300 HN repos
    random.seed(42)  # For reproducibility
    simulated_treatment = random.sample(potential_controls, sample_size)

    # Create DataFrames
    control_df = pd.DataFrame(filtered_controls)
    treatment_df = pd.DataFrame(simulated_treatment)

    # 5. Match control repositories to treatment repositories
    matched_controls = match_control_group(treatment_df, control_df, n_matches=control_ratio)

    # 6. Save results
    matched_controls.to_csv('control_repositories.csv', index=False)
    print(f"Selected {len(matched_controls)} control repositories")
    print(f"Results saved to control_repositories.csv")

    return matched_controls

# Example usage
if __name__ == "__main__":
    # Replace with the path to one of your metrics files
    metrics_file = "hn_stars_metrics.csv"

    # Call the main function
    control_repos = select_control_repositories(
        hn_repos_file=metrics_file,
        start_date="2022-01-01",
        end_date="2024-05-31",
        min_stars=5,
        control_ratio=2  # 2 control repos per treatment repo
    )