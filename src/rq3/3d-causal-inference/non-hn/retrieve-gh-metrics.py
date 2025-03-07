import os
import json
import time
import socket
import sys
import pandas as pd
import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from typing import Dict, Any, List

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Set your GitHub token as an environment variable
if not GITHUB_TOKEN:
    raise ValueError("Please set GITHUB_TOKEN environment variable")

INPUT_CSV_PATH = "./control_repositories.csv"  # Path to your input CSV file
CHECKPOINT_DIR = "./checkpoint"  # Directory to store checkpoints
OUTPUT_DIR = "./output"  # Directory to store output CSV files

# Create directories if they don't exist
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants for status codes
STATUS_DNE = -1  # Repository did not exist at the given date
STATUS_ERROR = -2  # Error occurred during data fetching

class GitHubGraphQLMetricsRetriever:
    """
    A class to retrieve historical GitHub repository metrics using the GraphQL API.
    """

    def __init__(self, github_token: str):
        """
        Initialize the retriever with a GitHub token.

        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
        self.headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
        }
        self.endpoint = 'https://api.github.com/graphql'

    def check_wifi_connection(self):
        """
        Check if connected to the internet via WiFi.
        If no connection, exit the program.
        """
        try:
            # Attempt to connect to a reliable external server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            print("\nNo WiFi connection detected. Exiting program.")
            sys.exit(1)  # Exit with error code 1

    def _execute_query(self, query: str, variables: Dict = None) -> Dict:
        """
        Execute a GraphQL query against GitHub's API.

        Args:
            query: GraphQL query string
            variables: Variables for the GraphQL query

        Returns:
            Dictionary containing the query result
        """
        if variables is None:
            variables = {}

        payload = {
            'query': query,
            'variables': variables
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload
            )

            # Check for rate limit headers
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

            if remaining <= 5:  # Buffer to prevent hitting rate limit
                current_time = time.time()
                sleep_duration = max(reset_time - current_time, 0) + 10  # Add buffer
                print(f"Rate limit almost reached. Sleeping for {sleep_duration:.2f} seconds.")
                time.sleep(sleep_duration)

            response.raise_for_status()
            result = response.json()

            if 'errors' in result:
                error_messages = ', '.join([error['message'] for error in result['errors']])
                print(f"GraphQL query errors: {error_messages}")
                return {'data': None, 'errors': result['errors']}

            return result

        except requests.RequestException as e:
            print(f"Error executing GraphQL query: {e}")
            return {'data': None, 'errors': [{'message': str(e)}]}

    def get_repo_info(self, owner: str, name: str) -> Dict:
        """
        Get basic repository information.

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Dictionary with repository info
        """
        query = """
        query GetRepoInfo($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            createdAt
            isArchived
            nameWithOwner
          }
        }
        """

        variables = {
            'owner': owner,
            'name': name
        }

        result = self._execute_query(query, variables)
        if result.get('data') and result['data'].get('repository'):
            return result['data']['repository']
        return None

    def extract_owner_repo(self, repo_url: str) -> tuple:
        """
        Extract owner and repository name from GitHub URL.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Tuple of (owner, repo_name)
        """
        parts = repo_url.rstrip('/').split('/')
        return parts[-2], parts[-1]

    def get_stars_at_date(self, owner: str, name: str, date: str) -> int:
        """
        Get the number of stars a repository had at a specific date.

        Args:
            owner: Repository owner
            name: Repository name
            date: Date string in ISO format (YYYY-MM-DDT23:59:59Z)

        Returns:
            Number of stars or STATUS_ERROR if an error occurred
        """
        query = """
        query GetStarsAtDate($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            stargazers(first: 100, after: $cursor) {
              totalCount
              pageInfo {
                endCursor
                hasNextPage
              }
              edges {
                starredAt
                node {
                  login
                }
              }
            }
          }
        }
        """

        target_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        variables = {
            'owner': owner,
            'name': name,
            'cursor': None
        }

        stars_count = 0
        has_next_page = True

        while has_next_page:
            result = self._execute_query(query, variables)

            if not result.get('data') or not result['data'].get('repository'):
                return STATUS_ERROR

            stargazers = result['data']['repository']['stargazers']

            # Process this page of stargazers
            for edge in stargazers['edges']:
                starred_at = datetime.strptime(edge['starredAt'], '%Y-%m-%dT%H:%M:%SZ')
                if starred_at <= target_date:
                    stars_count += 1
                else:
                    # If we've reached a stargazer that starred after our target date,
                    # we don't need to fetch more pages
                    has_next_page = False
                    break

            # Check if we need to fetch more pages
            if has_next_page and stargazers['pageInfo']['hasNextPage']:
                variables['cursor'] = stargazers['pageInfo']['endCursor']
            else:
                has_next_page = False

        return stars_count

    def get_forks_at_date(self, owner: str, name: str, date: str) -> int:
        """
        Get the number of forks a repository had at a specific date.

        Args:
            owner: Repository owner
            name: Repository name
            date: Date string in ISO format (YYYY-MM-DDT23:59:59Z)

        Returns:
            Number of forks or STATUS_ERROR if an error occurred
        """
        query = """
        query GetForksAtDate($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            forks(first: 100, after: $cursor) {
              totalCount
              pageInfo {
                endCursor
                hasNextPage
              }
              nodes {
                createdAt
              }
            }
          }
        }
        """

        target_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        variables = {
            'owner': owner,
            'name': name,
            'cursor': None
        }

        forks_count = 0
        has_next_page = True

        while has_next_page:
            result = self._execute_query(query, variables)

            if not result.get('data') or not result['data'].get('repository'):
                return STATUS_ERROR

            forks = result['data']['repository']['forks']

            # Count forks created before or on the target date
            for fork in forks['nodes']:
                created_at = datetime.strptime(fork['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
                if created_at <= target_date:
                    forks_count += 1
                else:
                    # If we've reached a fork created after our target date,
                    # we don't need to fetch more pages
                    has_next_page = False
                    break

            # Check if we need to fetch more pages
            if has_next_page and forks['pageInfo']['hasNextPage']:
                variables['cursor'] = forks['pageInfo']['endCursor']
            else:
                has_next_page = False

        return forks_count

    def get_commits_at_date(self, owner: str, name: str, date: str) -> int:
        """
        Get the number of commits a repository had at a specific date.

        Args:
            owner: Repository owner
            name: Repository name
            date: Date string in ISO format (YYYY-MM-DDT23:59:59Z)

        Returns:
            Number of commits or STATUS_ERROR if an error occurred
        """
        query = """
        query GetCommitsAtDate($owner: String!, $name: String!, $until: GitTimestamp!) {
          repository(owner: $owner, name: $name) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(until: $until) {
                    totalCount
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            'owner': owner,
            'name': name,
            'until': date
        }

        result = self._execute_query(query, variables)

        if not result.get('data') or not result['data'].get('repository') or not result['data']['repository'].get('defaultBranchRef'):
            return STATUS_ERROR

        return result['data']['repository']['defaultBranchRef']['target']['history']['totalCount']

    def get_prs_at_date(self, owner: str, name: str, date: str) -> int:
        """
        Get the number of pull requests a repository had at a specific date.

        Args:
            owner: Repository owner
            name: Repository name
            date: Date string in ISO format (YYYY-MM-DDT23:59:59Z)

        Returns:
            Number of PRs or STATUS_ERROR if an error occurred
        """
        query = """
        query GetPRsAtDate($owner: String!, $name: String!, $cursor: String) {
        repository(owner: $owner, name: $name) {
            pullRequests(first: 100, after: $cursor, states: [OPEN, CLOSED, MERGED], orderBy: {field: CREATED_AT, direction: ASC}) {
            totalCount
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                createdAt
            }
            }
        }
        }
            """

        target_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        variables = {
            'owner': owner,
            'name': name,
            'date': date
        }

        pr_count = 0
        has_next_page = True

        while has_next_page:
            result = self._execute_query(query, variables)

            if not result.get('data') or not result['data'].get('repository'):
                return STATUS_ERROR

            pull_requests = result['data']['repository']['pullRequests']

            # Count PRs created before or on the target date
            for pr in pull_requests['nodes']:
                created_at = datetime.strptime(pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
                if created_at <= target_date:
                    pr_count += 1
                else:
                    # If we've reached a PR created after our target date and we're
                    # requesting in ASC order, we can stop since all remaining will be newer
                    break

            # Check if we need to fetch more pages (and if the last PR was before our target date)
            if (pull_requests['pageInfo']['hasNextPage'] and
                created_at <= target_date):
                variables['cursor'] = pull_requests['pageInfo']['endCursor']
            else:
                has_next_page = False

        return pr_count

    def get_contributors_at_date(self, owner: str, name: str, date: str) -> int:
        """
        Get the number of contributors a repository had at a specific date.
        This is an approximation as GraphQL doesn't provide a direct way to count historical contributors.

        Args:
            owner: Repository owner
            name: Repository name
            date: Date string in ISO format (YYYY-MM-DDT23:59:59Z)

        Returns:
            Number of contributors or STATUS_ERROR if an error occurred
        """
        query = """
        query GetContributorsAtDate($owner: String!, $name: String!, $until: GitTimestamp!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 100, after: $cursor, until: $until) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      author {
                        user {
                          login
                        }
                        email
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            'owner': owner,
            'name': name,
            'until': date,
            'cursor': None
        }

        contributors = set()
        has_next_page = True

        while has_next_page:
            result = self._execute_query(query, variables)

            if not result.get('data') or not result['data'].get('repository') or not result['data']['repository'].get('defaultBranchRef'):
                return STATUS_ERROR

            history = result['data']['repository']['defaultBranchRef']['target']['history']

            # Extract contributors from commits
            for commit in history['nodes']:
                if commit['author']:
                    if commit['author'].get('user') and commit['author']['user'].get('login'):
                        contributors.add(commit['author']['user']['login'])
                    elif commit['author'].get('email'):
                        contributors.add(commit['author']['email'])

            # Check if we need to fetch more pages
            if history['pageInfo']['hasNextPage']:
                variables['cursor'] = history['pageInfo']['endCursor']
            else:
                has_next_page = False

        return len(contributors)

    def get_metrics_for_date(self, repo_url: str, target_date: datetime) -> Dict[str, Any]:
        """
        Retrieve repository metrics for a specific date.

        Args:
            repo_url: GitHub repository URL
            target_date: Target date for metrics

        Returns:
            Dictionary containing metrics
        """
        owner, repo = self.extract_owner_repo(repo_url)
        date_str = target_date.strftime('%Y-%m-%dT23:59:59Z')

        # Get repository info to check creation date
        repo_info = self.get_repo_info(owner, repo)

        if not repo_info:
            return {
                'stars': STATUS_ERROR,
                'commits': STATUS_ERROR,
                'pull_requests': STATUS_ERROR,
                'forks': STATUS_ERROR,
                'contributors': STATUS_ERROR
            }

        created_at = datetime.strptime(repo_info['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

        # If the repository didn't exist at the target date, return STATUS_DNE
        if created_at > target_date:
            return {
                'stars': STATUS_DNE,
                'commits': STATUS_DNE,
                'pull_requests': STATUS_DNE,
                'forks': STATUS_DNE,
                'contributors': STATUS_DNE
            }

        try:
            stars = self.get_stars_at_date(owner, repo, date_str)
            commits = self.get_commits_at_date(owner, repo, date_str)
            prs = self.get_prs_at_date(owner, repo, date_str)
            forks = self.get_forks_at_date(owner, repo, date_str)
            contributors = self.get_contributors_at_date(owner, repo, date_str)

            return {
                'stars': stars,
                'commits': commits,
                'pull_requests': prs,
                'forks': forks,
                'contributors': contributors
            }

        except Exception as e:
            print(f"Error getting metrics for {repo_url} at {date_str}: {e}")
            return {
                'stars': STATUS_ERROR,
                'commits': STATUS_ERROR,
                'pull_requests': STATUS_ERROR,
                'forks': STATUS_ERROR,
                'contributors': STATUS_ERROR
            }

    def _save_checkpoint(self, checkpoint_data: Dict, metric_name: str):
        """
        Save checkpoint for a specific metric.

        Args:
            checkpoint_data: Data to save
            metric_name: Name of the metric
        """
        filename = os.path.join(CHECKPOINT_DIR, f'{metric_name}_checkpoint.json')
        with open(filename, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def _load_checkpoint(self, metric_name: str) -> Dict:
        """
        Load checkpoint for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary containing checkpoint data or empty dict if not found
        """
        filename = os.path.join(CHECKPOINT_DIR, f'{metric_name}_checkpoint.json')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def process_repositories(self, csv_path: str, output_dir: str):
        """
        Process repositories and generate separate CSV files for each metric.

        Args:
            csv_path: Path to CSV file containing repository URLs
            output_dir: Directory to store output CSV files
        """
        # Read the input CSV file
        df = pd.read_csv(csv_path)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        print("DataFrame shape:", df.shape)
        print("Available columns:", df.columns.tolist())
        print("First few rows:")
        print(df.head())

        # Find URL and creation date columns
        url_column = None
        created_at_column = None

        for col in df.columns:
            if 'url' in col.lower():
                url_column = col
                print(f"Found URL column: '{col}'")
            elif 'created_at' in col.lower():
                created_at_column = col
                print(f"Found creation date column: '{col}'")

        if url_column is None:
            raise ValueError(f"No URL column found in CSV. Available columns: {df.columns.tolist()}")

        urls = df[url_column].str.strip().values

        if created_at_column:
            creation_dates = pd.to_datetime(df[created_at_column]).dt.tz_localize(None)
        else:
            creation_dates = None

        # Define date range
        chatgpt_release = datetime(2022, 5, 30)
        end_date = datetime(2025, 1, 31)
        all_dates = []
        current_date = chatgpt_release

        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += relativedelta(months=1)

        # Create DataFrames for each metric
        metrics = ['stars', 'commits', 'pull_requests', 'forks', 'contributors']
        metric_dfs = {
            metric: pd.DataFrame(
                index=urls,
                columns=[d.strftime('%Y-%m') for d in all_dates],
                dtype=float
            ) for metric in metrics
        }

        # Initialize metrics
        for metric_df in metric_dfs.values():
            metric_df.fillna(-1, inplace=True)

        # Load checkpoint data into metric_dfs
        for metric in metrics:
            checkpoint_data = self._load_checkpoint(metric)

            if checkpoint_data:
                for repo_url, date_values in checkpoint_data.items():
                    if repo_url in metric_dfs[metric].index:
                        for date_str, value in date_values.items():
                            if date_str in metric_dfs[metric].columns:
                                metric_dfs[metric].at[repo_url, date_str] = value

        # Process each repository
        progress_bar = tqdm(enumerate(urls), total=len(urls), desc="Processing repositories")

        for i, repo_url in progress_bar:
            repo_owner, repo_name = self.extract_owner_repo(repo_url)

            # Determine start date
            if creation_dates is not None:
                repo_creation = creation_dates.iloc[i]
                start_date = max(chatgpt_release, repo_creation)
            else:
                start_date = chatgpt_release

            repo_dates = [d for d in all_dates if d >= start_date]

            for date in repo_dates:
                date_str = date.strftime('%Y-%m')

                # Only process if any metric has error status (-2)
                # Useful if re-running the script after an error
                # if not any(metric_dfs[metric].at[repo_url, date_str] == -2 for metric in metrics):
                #     continue

                # Skip if data already exists in the DataFrame (from checkpoint)
                try:
                    for metric in metrics:
                        value = metric_dfs[metric].at[repo_url, date_str]
                        # print(f"Checking {metric} for {repo_url} at {date_str}: {value} (type: {type(value)})")

                    if all(metric_dfs[metric].at[repo_url, date_str] != -1 for metric in metrics):
                        continue
                except Exception as e:
                    print(f"Error checking data for {repo_url} at {date_str}: {e}")
                    print(f"Please check for duplicate entries in your GitHub URL csv dataset.")
                    return

                progress_bar.set_description(f"Processing {repo_owner}/{repo_name} for {date_str}")

                # Retrieve new metrics
                self.check_wifi_connection()
                metrics_data = self.get_metrics_for_date(repo_url, date)

                # Save to DataFrames
                for metric, value in metrics_data.items():
                    metric_dfs[metric].at[repo_url, date_str] = value

                # Save checkpoint
                for metric, value in metrics_data.items():
                    checkpoint_data = self._load_checkpoint(metric)

                    if repo_url not in checkpoint_data:
                        checkpoint_data[repo_url] = {}

                    checkpoint_data[repo_url][date_str] = value
                    self._save_checkpoint(checkpoint_data, metric)

        # Save results to CSV files
        for metric, df in metric_dfs.items():
            output_path = os.path.join(output_dir, f'{metric}_metrics.csv')
            df.to_csv(output_path)
            print(f"Saved {metric} metrics to {output_path}")

# Main execution
if __name__ == "__main__":
    retriever = GitHubGraphQLMetricsRetriever(GITHUB_TOKEN)
    retriever.process_repositories(csv_path=INPUT_CSV_PATH, output_dir=OUTPUT_DIR)
