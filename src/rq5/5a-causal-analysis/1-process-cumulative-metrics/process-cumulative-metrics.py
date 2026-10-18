import pandas as pd

file_path = "hn-stories-gh-ai-metadata-[6months-before-after-hn]-v2.csv"
df = pd.read_csv(file_path, encoding="utf-8")

print(df.columns.tolist())  # sanity check: do these match the names below?

df["month"] = pd.to_datetime(df["month"])
df = df.sort_values(["repo_full_name", "month"])  # cumsum depends on row order

# monthly column -> cumulative column name
cumulative_metrics = {
    "stars": "cumulative_stars",
    "forks": "cumulative_forks",
    "commits": "cumulative_commits",
    "PRs": "cumulative_prs",
    "contributors": "cumulative_contributors",
}

# groupby splits into one group per repo; cumsum restarts at each repo
cum = df.groupby("repo_full_name")[list(cumulative_metrics)].cumsum()

# rename the columns, then assign. Both share the same index, so pandas aligns rows
df[list(cumulative_metrics.values())] = cum.rename(columns=cumulative_metrics)

df.to_csv("hn-stories-gh-ai-metrics-[6months-before-after-hn]-cumulative-v2.csv", index=False)