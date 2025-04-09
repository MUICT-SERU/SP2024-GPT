import os
import requests
import datetime

def get_github_metrics(owner: str, repo: str, year: int, month: int):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token not found in environment variables.")

    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

    query = """
        query GetRepoMetrics($owner: String!, $repo: String!, $start: GitTimestamp, $end: GitTimestamp) {
  repository(owner: $owner, name: $repo) {
    stargazers {
      totalCount
    }
    forks {
      totalCount
    }
    pullRequests {
      totalCount
    }
    defaultBranchRef {
      target {
        ... on Commit {
          history(since: $start, until: $end) {
            totalCount
          }
        }
      }
    }
  }
}

    """

    variables = {
        "owner": owner,
        "repo": repo,
        "start": start_date.isoformat() + "T00:00:00Z",
        "end": end_date.isoformat() + "T00:00:00Z",
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"GitHub API error: {response.status_code}, {response.text}")

if __name__ == "__main__":
    owner = "GoogleCloudPlatform"
    repo = "vertex-ai-samples"
    year = 2023
    month = 1

    metrics = get_github_metrics(owner, repo, year, month)
    print(metrics)
