"""
Fetch CURRENT (today) cumulative metrics for a list of GitHub repos,
using the free GitHub API (no BigQuery needed).

Metrics:
    star_count        - live stargazer count
    fork_count        - live fork count
    contributor_count - via the Link-header page-count trick (REST)
    commit_count      - total commits on the default branch (GraphQL)
    pr_count          - total PRs ever opened, any state (GraphQL)

Setup:
    pip install requests pandas
    Create a free token at https://github.com/settings/tokens
      (classic token, no scopes needed for public repos)
    export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

Usage:
    python fetch_github_metrics.py --input treatment_repos.csv --output treatment_metrics_today.csv

Input CSV just needs a `repo_full_name` column (owner/repo format) --
matches both your treatment and control CSV formats.

Resumable: if interrupted (e.g. rate limit), rerun with the same
--output file and it will skip repos already written.
"""

import argparse
import csv
import os
import sys
from tqdm import tqdm
import time

import pandas as pd
import requests

GRAPHQL_URL = "https://api.github.com/graphql"
REST_BASE = "https://api.github.com/repos"
BATCH_SIZE = 50  # repos per GraphQL call


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN environment variable first (see script docstring).")
    return token


def check_rate_limit(headers: dict) -> None:
    """Sleep until reset if we're close to running out of requests."""
    resp = requests.get("https://api.github.com/rate_limit", headers=headers)
    remaining = resp.json()["resources"]["core"]["remaining"]
    reset_at = resp.json()["resources"]["core"]["reset"]
    if remaining < 20:
        wait = max(reset_at - time.time(), 0) + 5
        print(f"Rate limit nearly exhausted ({remaining} left). Sleeping {wait:.0f}s...")
        time.sleep(wait)


def fetch_batch_graphql(repos: list, headers: dict) -> dict:
    """
    One GraphQL call for up to BATCH_SIZE repos: stars, forks, PR count,
    and default-branch commit count. Returns {repo_full_name: {...}}.
    """
    fragments = []
    for i, repo_full_name in tqdm(enumerate(repos), desc="Fetching GraphQL data"):
        owner, name = repo_full_name.split("/", 1)
        fragments.append(f'''
        repo{i}: repository(owner: "{owner}", name: "{name}") {{
          nameWithOwner
          stargazerCount
          forkCount
          pullRequests {{ totalCount }}
          defaultBranchRef {{
            target {{
              ... on Commit {{ history {{ totalCount }} }}
            }}
          }}
        }}''')
    query = "query {" + "".join(fragments) + "\n}"

    resp = requests.post(GRAPHQL_URL, json={"query": query}, headers=headers)
    resp.raise_for_status()
    data = resp.json().get("data", {})

    results = {}
    for i, repo_full_name in enumerate(repos):
        node = data.get(f"repo{i}")
        if node is None:
            # repo renamed, deleted, or made private -- flag as missing
            results[repo_full_name] = {
                "star_count": None, "fork_count": None,
                "commit_count": None, "pr_count": None,
            }
            continue
        default_ref = node.get("defaultBranchRef")
        commit_count = None
        if default_ref and default_ref.get("target"):
            commit_count = default_ref["target"].get("history", {}).get("totalCount")
        results[repo_full_name] = {
            "star_count": node.get("stargazerCount"),
            "fork_count": node.get("forkCount"),
            "commit_count": commit_count,
            "pr_count": node.get("pullRequests", {}).get("totalCount"),
        }
    return results


def fetch_contributor_count(repo_full_name: str, headers: dict) -> int:
    """
    REST trick: per_page=1 means each page = 1 contributor, so the
    highest page number in the Link header = total contributor count.
    anon=1 includes anonymous/non-GitHub-account commit authors.
    """
    url = f"{REST_BASE}/{repo_full_name}/contributors"
    resp = requests.get(url, headers=headers, params={"per_page": 1, "anon": 1})
    if resp.status_code == 404:
        return None  # repo renamed/deleted/private
    resp.raise_for_status()

    link = resp.headers.get("Link")
    if not link:
        # No pagination header means 0 or 1 contributor total
        return len(resp.json())

    for part in link.split(","):
        if 'rel="last"' in part:
            last_url = part[part.find("<") + 1: part.find(">")]
            last_page = last_url.split("page=")[-1].split("&")[0]
            return int(last_page)
    return len(resp.json())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="CSV with a repo_full_name column")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    repos_df = pd.read_csv(args.input)
    all_repos = repos_df["repo_full_name"].dropna().unique().tolist()

    already_done = set()
    if os.path.exists(args.output):
        already_done = set(pd.read_csv(args.output)["repo_full_name"])
        print(f"Resuming: {len(already_done)} repos already fetched.")

    remaining = [r for r in all_repos if r not in already_done]
    print(f"{len(remaining)} repos left to fetch.")

    write_header = not os.path.exists(args.output)
    with open(args.output, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["repo_full_name", "star_count", "fork_count",
                              "contributor_count", "commit_count", "pr_count"])

        for start in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[start:start + BATCH_SIZE]
            check_rate_limit(headers)

            try:
                gql_results = fetch_batch_graphql(batch, headers)
            except requests.HTTPError as e:
                print(f"GraphQL batch failed at repo {start}: {e}. Skipping batch.")
                continue

            for repo_full_name in batch:
                check_rate_limit(headers)
                try:
                    contributor_count = fetch_contributor_count(repo_full_name, headers)
                except requests.HTTPError as e:
                    print(f"Contributor fetch failed for {repo_full_name}: {e}")
                    contributor_count = None

                m = gql_results.get(repo_full_name, {})
                writer.writerow([
                    repo_full_name,
                    m.get("star_count"), m.get("fork_count"),
                    contributor_count, m.get("commit_count"), m.get("pr_count"),
                ])
            f.flush()
            print(f"Fetched {min(start + BATCH_SIZE, len(remaining))}/{len(remaining)}")

    print(f"Done. Results in {args.output}")


if __name__ == "__main__":
    main()