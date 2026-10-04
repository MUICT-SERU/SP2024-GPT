# %% [markdown]
# # filter_treatment_repos_for_did.py

# %%
"""
filter_treatment_repos_for_did.py

CRITERIA (a repo must pass ALL, applied in this order)
------------------------------------------------------
  1. has metadata            -> we know its creation date
  2. age                     -> created >= MIN_AGE_DAYS before HN submission
                                (unchanged from the old script)
  3. pre-window covered      -> HN month - PRE_MONTHS  >= panel start   (NEW)
  4. post-window covered     -> HN month + POST_MONTHS <= panel end
                                (replaces the hard-coded 2024-06-01 cutoff,
                                 so it adapts if the panel is extended)

The script prints a "funnel" showing how many repos each criterion removes,
which is handy for the paper's data-selection description.

TWO IDEAS WORTH UNDERSTANDING
-----------------------------
* pandas Period ('2024-03'): a calendar month as a real type. Comparing
  months as Periods avoids the timestamp trap where '2024-03-01' (a month
  label) is < '2024-03-19 20:32' (an HN timestamp) even though both are
  "March". Period arithmetic (p - 6) also handles year boundaries.
* Vectorised filtering: instead of looping over repos and calling a function
  each time, we build one row per repo (a table) and express each criterion
  as a boolean column. It is shorter, faster, and the funnel falls out
  naturally.
"""

# %%
import pandas as pd

# ============================================================
# CONFIG
# ============================================================
METRICS_FILE = "hn-stories-gh-ai-metrics.csv"
METADATA_FILE = "hn-stories-gh-ai-metadata.csv"
OUT_METRICS_FILE = "filtered_metrics_for_did_v2.csv"
OUT_METADATA_FILE = "filtered_metadata_for_did_v2.csv"

MIN_AGE_DAYS = 180   # kept from the old script (~6 months)
PRE_MONTHS = 6       # need t-6 ... t-1
POST_MONTHS = 6      # need t+1 ... t+6


# %%
# ============================================================
# 1. LOAD + NORMALISE DATES
# ============================================================
metrics_df = pd.read_csv(METRICS_FILE)
metadata_df = pd.read_csv(METADATA_FILE)

# utc=True parses mixed/tz-aware strings safely; tz_localize(None) then drops
# the timezone so every date in the script is a plain (naive) timestamp.
def to_naive(s):
    return pd.to_datetime(s, utc=True).dt.tz_localize(None)

metrics_df["month"] = to_naive(metrics_df["month"])
metrics_df["hn_submission_date"] = to_naive(metrics_df["hn_submission_date"])
metadata_df["repo_creation_date"] = to_naive(metadata_df["repo_creation_date"])

# The panel's own edges, read from the data instead of hard-coded.
panel_start = metrics_df["month"].dt.to_period("M").min()
panel_end = metrics_df["month"].dt.to_period("M").max()
print(f"Panel covers {panel_start} .. {panel_end}")


# %%
# ============================================================
# 2. ONE ROW PER REPO
# ============================================================
# Earliest HN submission per repo (same rule as the old script).
repos = (metrics_df.groupby("repo_full_name")["hn_submission_date"]
                   .min()
                   .rename("hn_submission_date")
                   .reset_index())
repos["hn_month"] = repos["hn_submission_date"].dt.to_period("M")

# Left-join creation dates: repos without metadata get NaT, not dropped yet,
# so the funnel can count them.
repos = repos.merge(metadata_df[["repo_full_name", "repo_creation_date"]]
                    .drop_duplicates("repo_full_name"),
                    on="repo_full_name", how="left")


# %%
# ============================================================
# 3. THE CRITERIA AS BOOLEAN COLUMNS
# ============================================================
repos["c1_has_metadata"] = repos["repo_creation_date"].notna()

age_days = (repos["hn_submission_date"] - repos["repo_creation_date"]).dt.days
repos["c2_old_enough"] = age_days >= MIN_AGE_DAYS      # NaT -> False

repos["c3_pre_covered"] = (repos["hn_month"] - PRE_MONTHS) >= panel_start
repos["c4_post_covered"] = (repos["hn_month"] + POST_MONTHS) <= panel_end

criteria = ["c1_has_metadata", "c2_old_enough", "c3_pre_covered", "c4_post_covered"]

# .all(axis=1) is True only when every criterion column is True in that row.
repos["qualified"] = repos[criteria].all(axis=1)


# %%
# ============================================================
# 4. FUNNEL REPORT (sequential: each step shows what is LEFT)
# ============================================================
print(f"\nTotal repositories: {len(repos)}")
remaining = pd.Series(True, index=repos.index)
for c in criteria:
    before = int(remaining.sum())
    remaining &= repos[c]
    after = int(remaining.sum())
    print(f"  after {c:<18}: {after:>4}  (dropped {before - after})")

n_q = int(repos["qualified"].sum())
print(f"\nQualified repositories: {n_q} "
      f"({n_q / len(repos) * 100:.2f}% of {len(repos)})")


# %%
# ============================================================
# 5. SANITY CHECK: do the rows really exist in the panel?
# ============================================================
# Criteria 3/4 are arithmetic on the panel's edges. That only guarantees
# real data if the panel has no missing months for a repo. Verify it.
qualified = repos[repos["qualified"]]
metrics_df["_period"] = metrics_df["month"].dt.to_period("M")
months_present = metrics_df.groupby("repo_full_name")["_period"].agg(set)

incomplete = []
for repo, hn_month in zip(qualified["repo_full_name"], qualified["hn_month"]):
    needed = set(pd.period_range(hn_month - PRE_MONTHS, hn_month + POST_MONTHS, freq="M"))
    if not needed <= months_present[repo]:
        incomplete.append(repo)

if incomplete:
    print(f"\n[!] {len(incomplete)} qualified repos are missing rows inside "
          f"t-{PRE_MONTHS}..t+{POST_MONTHS}: {incomplete[:5]} ...")
    print("    (the panel has month gaps for them -- decide whether to drop them)")
else:
    print(f"\nSanity check passed: every qualified repo has all months "
          f"t-{PRE_MONTHS}..t+{POST_MONTHS} in the panel.")


# %%
# ============================================================
# 6. SAVE
# ============================================================
qualified_repos = set(qualified["repo_full_name"])
metrics_df.drop(columns="_period").loc[
    metrics_df["repo_full_name"].isin(qualified_repos)
].to_csv(OUT_METRICS_FILE, index=False)
metadata_df[metadata_df["repo_full_name"].isin(qualified_repos)].to_csv(
    OUT_METADATA_FILE, index=False)
print(f"Wrote {OUT_METRICS_FILE} and {OUT_METADATA_FILE}")


# %%
# ============================================================
# 7. SPOT-CHECK A FEW QUALIFIED REPOS
# ============================================================
print("\nSample of qualified repositories:")
for _, r in qualified.head(5).iterrows():
    n_post = sum(p >= r["hn_month"] for p in months_present[r["repo_full_name"]])
    age_m = (r["hn_submission_date"] - r["repo_creation_date"]).days / 30
    print(f"{r['repo_full_name']}: created {age_m:.1f} months before HN, "
          f"HN month {r['hn_month']}, {n_post} panel months from HN month onward")