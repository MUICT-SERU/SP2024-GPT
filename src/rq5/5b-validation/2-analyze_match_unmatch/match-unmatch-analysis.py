# %% [markdown]
# # setup

# %%
"""
matched_vs_unmatched_analysis.py

QUESTION THIS ANSWERS
----------------------
For each metric, we matched a subset of treatment (HN-submitted) repos to
control repos. This script checks whether the repos that got MATCHED look
systematically different from the ones that were AVAILABLE but not matched
-- i.e. a representativeness / balance diagnostic, done separately for the
treatment side and the control side.

This is *not* the parallel-trends check (that's your event-study code) --
it's a sanity check on sample selection: "does matching quietly select for
unusually big/small/active repos?"

SUMMARY STATISTIC USED PER REPO
--------------------------------
Each repo's monthly panel is collapsed to ONE number before plotting:
  - for a "new_X" (flow) metric  -> sum over the observed window
  - for a "cumulative_X" (stock) metric -> the max value in the window
    (its final accumulated total)
Per your caveat, cumulative_X is just a running sum of new_X, so these two
are conceptually the same "how much activity did this repo generate"
number -- we just pick the right aggregation for each column type so we
don't double count.

OUTPUTS
-------
plots/matched_vs_unmatched/<metric>_box_violin.png   (per metric)
plots/matched_vs_unmatched/<metric>_ecdf.png         (per metric)
plots/matched_vs_unmatched/love_plot_smd.png         (one summary figure)
plots/matched_vs_unmatched/balance_table.csv         (numbers behind the love plot)
"""

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import textwrap

# ============================================================
# CONFIG -- double-check these five things before running
# ============================================================

DATASET_DIR = Path(".")
MATCH_DIR = Path(".")  # wherever matched_control_<metric>.csv live

# NOTE: going by your earlier notebook (match-parallel-trend-assumption.ipynb),
# "hn-stories-..." = TREATMENT (HN-submitted repos) and "nonhn-..." = CONTROL.
# Your message labeled them the other way round -- swap these two lines back
# if that was intentional and not a typo.
TREATMENT_METRICS_FILE = DATASET_DIR / "hn-stories-gh-ai-metrics-cumulative.csv"
CONTROL_METRICS_FILE = DATASET_DIR / "nonhn-gh-ai-metrics-cumulative.csv"

TREATMENT_REPO_COL = "repo_full_name"  # column identifying a repo in the treatment file
CONTROL_REPO_COL = "control_repo"      # column identifying a repo in the control file

MONTHLY_METRICS = ['new_forks', 'new_stars', 'new_commits', 'new_prs', 'active_contributors']
CUMULATIVE_METRICS = ['cumulative_stars', 'cumulative_forks', 'cumulative_commits',
                       'cumulative_prs', 'cumulative_ve_contributors']
ALL_METRICS = MONTHLY_METRICS + CUMULATIVE_METRICS

OUTPUT_DIR = Path("plots/matched_vs_unmatched")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)

# Set global aesthetic settings
plt.rcParams.update({'font.size': 10})


# %%
# ============================================================
# 1. LOAD DATA
# ============================================================

def load_metrics_panels():
    """Load the two long-format panels once, up front, so we don't
    re-read 150k-row CSVs inside a per-metric loop."""
    treatment_metrics = pd.read_csv(TREATMENT_METRICS_FILE)
    control_metrics = pd.read_csv(CONTROL_METRICS_FILE)
    return treatment_metrics, control_metrics


def load_matched_repo_sets(metric):
    """matched_control_<metric>.csv has one row per matched pair.
    We only need *which repos* were matched, as two sets."""
    path = MATCH_DIR / f"matched_control_{metric}.csv"
    df = pd.read_csv(path)
    return set(df['treatment_repo']), set(df['control_repo'])

# %%

# ============================================================
# 2. COLLAPSE EACH REPO'S PANEL TO ONE COMPARABLE NUMBER
# ============================================================

def summarize_repo_metric(metrics_df, repo_col, metric_col, is_cumulative):
    """One row per repo: total observed activity for `metric_col`
    across the whole panel window."""
    agg_func = 'max' if is_cumulative else 'sum'
    out = (metrics_df.groupby(repo_col)[metric_col]
                      .agg(agg_func)
                      .rename('total_value')
                      .reset_index()
                      .rename(columns={repo_col: 'repo'}))
    return out


def build_comparison_df(treatment_metrics, control_metrics, metric):
    """Tidy frame for one metric: repo | group | matched | total_value."""
    is_cumulative = metric in CUMULATIVE_METRICS
    matched_treat, matched_ctrl = load_matched_repo_sets(metric)

    treat = summarize_repo_metric(treatment_metrics, TREATMENT_REPO_COL, metric, is_cumulative)
    treat['group'] = 'treatment'
    treat['matched'] = treat['repo'].isin(matched_treat)

    ctrl = summarize_repo_metric(control_metrics, CONTROL_REPO_COL, metric, is_cumulative)
    ctrl['group'] = 'control'
    ctrl['matched'] = ctrl['repo'].isin(matched_ctrl)

    df = pd.concat([treat, ctrl], ignore_index=True)
    df['matched_label'] = df['matched'].map({True: 'matched', False: 'unmatched'})
    # log1p makes heavy-tailed count data readable without dropping zeros
    df['log1p_value'] = np.log1p(df['total_value'])
    return df


# %%
METRIC_LABELS = {
    'new_stars': 'New Stars',
    'new_forks': 'New Forks',
    'new_commits': 'New Commits',
    'new_prs': 'New PRs',
    'active_contributors': 'New Active Contributors',
    'cumulative_stars': 'Cumulative Stars',
    'cumulative_forks': 'Cumulative Forks',
    'cumulative_commits': 'Cumulative Commits',
    'cumulative_prs': 'Cumulative PRs',
    'cumulative_ve_contributors': 'Cumulative Contributors',
}

def pretty(metric_original):
    return METRIC_LABELS.get(metric_original)

# %% [markdown]
# # box plot

# %%
# ============================================================
# 3. VISUAL 1 -- boxplot and violin plot, as separate figures,
#    on the RAW (not log-transformed) scale.
#    NOTE: raw scale means a handful of extreme repos will stretch
#    the y-axis and compress everything else near the bottom --
#    that's the known tradeoff of dropping the log transform.
# ============================================================

def plot_boxplot(df, metric):
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.boxplot(data=df, x='group', y='total_value', hue='matched_label',
                ax=ax, showfliers=True)
    ax.set_title(pretty(metric + " -- boxplot"))
    ax.set_ylabel(pretty(metric))
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{metric}_boxplot.pdf", dpi=150)
    plt.close(fig)


def plot_violinplot(df, metric):
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.violinplot(data=df, x='group', y='total_value', hue='matched_label',
                    ax=ax, split=True, inner='quartile', cut=0)
    ax.set_title(pretty(metric + " -- violin plot"))
    ax.set_ylabel(pretty(metric))
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{metric}_violin.pdf", dpi=150)
    plt.close(fig)



# %% [markdown]
# # ECDF

# %%


# ============================================================
# 4. VISUAL 2 -- ECDF, per metric, per group
# ============================================================

def ecdf(values):
    x = np.sort(values)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y

def plot_ecdf(df, metric):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, group in zip(axes, ['treatment', 'control']):
        sub = df[df['group'] == group]
        for label, color in [('matched', 'tab:blue'), ('unmatched', 'tab:orange')]:
            vals = sub.loc[sub['matched_label'] == label, 'log1p_value']
            if len(vals) == 0:
                continue
            x, y = ecdf(vals)
            ax.plot(x, y, label=f"{label} (n={len(vals)})", color=color, linewidth=2)
        ax.set_title(f"{pretty(metric)} -- {group}")
        ax.set_xlabel("log1p(total activity)")
        ax.legend()
    axes[0].set_ylabel("cumulative proportion of repos")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{metric}_ecdf.pdf", dpi=150)
    plt.close(fig)


# %% [markdown]
# # love plot

# %%
# ============================================================
# 5. SUMMARY -- standardized mean difference + love plot
# ============================================================

def standardized_mean_diff(a, b):
    """Cohen's-d style SMD between two samples on the log1p scale.
    |SMD| < 0.1 is the common 'good balance' rule of thumb (Austin, 2011)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    pooled_std = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    if pooled_std == 0 or np.isnan(pooled_std):
        return 0.0
    return (a.mean() - b.mean()) / pooled_std


def build_balance_table(treatment_metrics, control_metrics):
    rows = []
    for metric in ALL_METRICS:
        df = build_comparison_df(treatment_metrics, control_metrics, metric)
        for group in ['treatment', 'control']:
            sub = df[df['group'] == group]
            matched_vals = sub.loc[sub['matched'], 'log1p_value']
            unmatched_vals = sub.loc[~sub['matched'], 'log1p_value']
            rows.append({
                'metric': metric,
                'group': group,
                'n_matched': len(matched_vals),
                'n_unmatched': len(unmatched_vals),
                'mean_matched': matched_vals.mean() if len(matched_vals) else np.nan,
                'mean_unmatched': unmatched_vals.mean() if len(unmatched_vals) else np.nan,
                'smd': standardized_mean_diff(matched_vals, unmatched_vals),
            })
    return pd.DataFrame(rows)


def plot_love_plot(balance_df):
    fig, ax = plt.subplots(figsize=(8, 6))
    balance_df = balance_df.sort_values(['metric', 'group'])
    y_labels = [f"{m} ({g})" for m, g in zip(balance_df['metric'], balance_df['group'])]
    y_pos = np.arange(len(balance_df))

    colors = balance_df['group'].map({'treatment': 'tab:blue', 'control': 'tab:orange'})
    ax.scatter(balance_df['smd'], y_pos, c=colors, s=60, zorder=3)

    # show legend bottom left outside the graph
    ax.legend(handles=[
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='tab:blue', markersize=10, label='treatment'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='tab:orange', markersize=10, label='control')
    ], loc='lower left', bbox_to_anchor=(-0.5, -0.15))

    ax.axvline(0, color='black', linewidth=1)
    ax.axvline(0.1, color='red', linestyle='--', linewidth=1)
    ax.axvline(-0.1, color='red', linestyle='--', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Standardized Mean Difference (matched - unmatched)")
    ax.set_title("Balance check: matched vs. unmatched repos\n(dashed lines = |SMD| = 0.1 threshold)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "love_plot_smd.pdf", dpi=150)
    plt.close(fig)


# %% [markdown]
# # stats

# %%
# ============================================================
# 6. DESCRIPTIVE STATS -- min/max/mean/stdev per repo, for the
#    whole control pool, whole treatment pool, and both combined.
#    This is population description (not a matched-vs-unmatched
#    diagnostic like section 5) -- useful for a "Table 1" style
#    dataset-characteristics table in the paper.
# ============================================================

# metric -> how to collapse each repo's monthly panel to one number.
#   'max'  for cumulative (stock) metrics: the final accumulated total.
#   'mean' for active_contributors: average monthly active-contributor
#           count per repo. NOT 'sum' -- summing headcounts across
#           months would double-count the same contributor appearing
#           active in multiple months.
DESCRIPTIVE_METRICS = {
    'cumulative_commits': 'max',
    'cumulative_forks': 'max',
    'cumulative_prs': 'max',
    'cumulative_stars': 'max',
    'active_contributors': 'mean',
}


def repo_level_values(metrics_df, repo_col, metric_col, agg):
    """One value per repo (see DESCRIPTIVE_METRICS for which aggregation)."""
    return metrics_df.groupby(repo_col)[metric_col].agg(agg)

def build_descriptive_stats_table(treatment_metrics, control_metrics):
    """For every metric in ALL_METRICS, compute min/max/mean/stdev across
    four slices: matched treatment, matched control, matched treatment+
    control combined, and unmatched (treatment+control combined)."""
    rows = []
    for metric in ALL_METRICS:
        df = build_comparison_df(treatment_metrics, control_metrics, metric)

        slices = {
            'matched_treatment': df[(df['group'] == 'treatment') & df['matched']],
            'matched_control':   df[(df['group'] == 'control') & df['matched']],
            'matched_combined':  df[df['matched']],
            'unmatched':         df[~df['matched']],
        }
        for dataset_label, sub in slices.items():
            vals = sub['total_value']
            rows.append({
                'metric': metric,
                'dataset': dataset_label,
                'n_repos': len(vals),
                'min': vals.min() if len(vals) else np.nan,
                'max': vals.max() if len(vals) else np.nan,
                'mean': vals.mean() if len(vals) else np.nan,
                'stdev': vals.std(ddof=1) if len(vals) > 1 else np.nan,
            })
    return pd.DataFrame(rows)

# %% [markdown]
# # run

# %%
# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    treatment_metrics, control_metrics = load_metrics_panels()

    for metric in ALL_METRICS:
        print(f"Processing {metric} ...")
        df = build_comparison_df(treatment_metrics, control_metrics, metric)
        plot_boxplot(df, metric)
        plot_violinplot(df, metric)
        plot_ecdf(df, metric)

    balance_df = build_balance_table(treatment_metrics, control_metrics)
    balance_df.to_csv(OUTPUT_DIR / "balance_table.csv", index=False)
    plot_love_plot(balance_df)

    print(f"\nDone with matched-vs-unmatched diagnostics. Outputs in: {OUTPUT_DIR.resolve()}")
    print(balance_df[['metric', 'group', 'n_matched', 'n_unmatched', 'smd']]
          .to_string(index=False))

    descriptive_df = build_descriptive_stats_table(treatment_metrics, control_metrics)
    descriptive_df.to_csv(OUTPUT_DIR / "descriptive_stats_table.csv", index=False)

    print("\nDescriptive statistics (control / treatment / combined):")
    print(descriptive_df.to_string(index=False))

# %% [markdown]
# # cross check

# %%
"""
crosscheck_matched_counts.py

PURPOSE
-------
Sanity-check that the "n_matched" counts in balance_table.csv actually
match the number of distinct repos found in each matched_control_<metric>.csv
pairing file. This is a standalone diagnostic -- it does not touch or
re-run the main analysis script.

WHY THEY COULD DISAGREE
------------------------
balance_table.csv's n_matched comes from: take the full treatment (or
control) metrics panel, tag each repo True/False by whether its name
appears in matched_control_<metric>.csv, then count the True rows.

If a repo name in the match file doesn't exist in the metrics panel
(whitespace, capitalization, a renamed/deleted repo, etc.), it silently
contributes ZERO to that count -- so a mismatch almost always means
balance_table's count is LOWER than the match file's unique-repo count,
never higher. This script flags exactly that, and (if the metrics panel
files are available) names the specific missing repos.

WHAT COUNTS ARE COMPARED
-------------------------
Per metric, per side (treatment / control):
  expected_from_match_file  = nunique(repo) in matched_control_<metric>.csv
  reported_in_balance_table = n_matched, as already computed in balance_table.csv

Note treatment and control are NOT expected to have the same count as
each other -- matching here is many-to-one (a control repo can be reused
across several treatment repos), so nunique(control_repo) is often
smaller than nunique(treatment_repo)/n_pair_rows. That's normal, not a
bug. What SHOULD match is each side against its own balance_table row.

USAGE
-----
Put this script in the same folder as:
  - balance_table.csv
  - matched_control_<metric>.csv  (as many of the 10 as you have)
and optionally the two full metrics panels (for the repo-name drill-down).
Then just run: python crosscheck_matched_counts.py
"""

import pandas as pd
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
MATCH_DIR = Path(".")
BALANCE_TABLE_PATH = Path("balance_table.csv")

# Optional: only needed for the repo-name drill-down on a mismatch.
# If these paths don't exist, that step is skipped automatically.
TREATMENT_METRICS_FILE = Path("hn-stories-gh-ai-metrics-cumulative.csv")
CONTROL_METRICS_FILE = Path("nonhn-gh-ai-metrics-cumulative.csv")
TREATMENT_REPO_COL = "repo_full_name"
CONTROL_REPO_COL = "control_repo"

MONTHLY_METRICS = ['new_forks', 'new_stars', 'new_commits', 'new_prs', 'active_contributors']
CUMULATIVE_METRICS = ['cumulative_stars', 'cumulative_forks', 'cumulative_commits',
                       'cumulative_prs', 'cumulative_ve_contributors']
ALL_METRICS = MONTHLY_METRICS + CUMULATIVE_METRICS


# ============================================================
# 1. Read what the match file itself says
# ============================================================

def load_match_file_counts(metric):
    """Ground-truth counts straight from matched_control_<metric>.csv.
    Returns None if that file isn't present."""
    path = MATCH_DIR / f"matched_control_{metric}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return {
        'metric': metric,
        'n_pair_rows': len(df),
        'n_unique_treatment': df['treatment_repo'].nunique(),
        'n_unique_control': df['control_repo'].nunique(),
        'n_treatment_dupe_rows': int(df['treatment_repo'].duplicated().sum()),
        'n_control_dupe_rows': int(df['control_repo'].duplicated().sum()),
        '_treatment_repos': set(df['treatment_repo']),
        '_control_repos': set(df['control_repo']),
    }


def load_reported_counts(balance_df, metric):
    """n_matched (treatment, control) as already reported in balance_table.csv."""
    sub = balance_df[balance_df['metric'] == metric]
    return {row['group']: int(row['n_matched']) for _, row in sub.iterrows()}


# ============================================================
# 2. Compare the two
# ============================================================

def crosscheck():
    balance_df = pd.read_csv(BALANCE_TABLE_PATH)
    rows = []
    missing_match_files = []

    for metric in ALL_METRICS:
        file_counts = load_match_file_counts(metric)
        if file_counts is None:
            missing_match_files.append(metric)
            continue

        reported = load_reported_counts(balance_df, metric)

        for group, file_key in [('treatment', 'n_unique_treatment'),
                                 ('control', 'n_unique_control')]:
            expected = file_counts[file_key]
            actual = reported.get(group)
            rows.append({
                'metric': metric,
                'group': group,
                'expected_from_match_file': expected,
                'reported_in_balance_table': actual,
                'match': (actual == expected),
                'diff': (None if actual is None else actual - expected),
            })

    result_df = pd.DataFrame(rows)

    print("=" * 78)
    print("CROSS-CHECK: matched_control_<metric>.csv  vs  balance_table.csv")
    print("=" * 78)
    print(result_df.to_string(index=False))

    if missing_match_files:
        print(f"\n[!] No matched_control_<metric>.csv found for: {missing_match_files}"
              f"\n    (place them in MATCH_DIR to include them in the check)")

    n_mismatch = int((~result_df['match']).sum())
    if n_mismatch == 0 and not missing_match_files:
        print("\nAll counts agree. \u2714")
    elif n_mismatch == 0:
        print(f"\nAll {len(result_df)} available comparisons agree "
              f"(but {len(missing_match_files)} metric(s) couldn't be checked -- see above).")
    else:
        print(f"\n{n_mismatch} mismatch(es) found:")
        print(result_df[~result_df['match']].to_string(index=False))

    return result_df


# ============================================================
# 3. If something's off, name the actual repos causing it
# ============================================================

def diagnose_missing_repos(metric):
    """For one metric, list match-file repo names absent from the metrics
    panel -- the usual cause of a mismatch. Needs the panel files."""
    if not (TREATMENT_METRICS_FILE.exists() and CONTROL_METRICS_FILE.exists()):
        print(f"\n({metric}: metrics panel files not found locally -- "
              f"can't drill into which repo names are missing.)")
        return

    file_counts = load_match_file_counts(metric)
    if file_counts is None:
        return

    treatment_panel_repos = set(pd.read_csv(TREATMENT_METRICS_FILE)[TREATMENT_REPO_COL])
    control_panel_repos = set(pd.read_csv(CONTROL_METRICS_FILE)[CONTROL_REPO_COL])

    missing_treatment = file_counts['_treatment_repos'] - treatment_panel_repos
    missing_control = file_counts['_control_repos'] - control_panel_repos

    print(f"\n--- {metric}: match-file repos NOT found in the metrics panel ---")
    print(f"treatment: {sorted(missing_treatment) if missing_treatment else '(none)'}")
    print(f"control:   {sorted(missing_control) if missing_control else '(none)'}")


if __name__ == "__main__":
    result_df = crosscheck()
    result_df.to_csv("matched_count_crosscheck.csv", index=False)

    mismatched_metrics = result_df.loc[~result_df['match'], 'metric'].unique()
    for metric in mismatched_metrics:
        diagnose_missing_repos(metric)

# %%



