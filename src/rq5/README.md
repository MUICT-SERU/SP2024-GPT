# RQ5: Causal Effect of Hacker News on GitHub Growth

This RQ is part of the extended version of the paper (TOSEM submission, under review) and is not in the ICSME 2025 paper.

## RQ5a - Causal Analysis (Matching and Difference-in-Differences)
Folder: [`5a-causal-analysis/`](5a-causal-analysis/)

Estimate the causal effect of an HN submission on GitHub repository growth. Each HN-submitted AI repository (treatment) is matched with a similar AI repository that was not submitted to HN (control), then the difference-in-differences (DiD) is estimated. The analysis is done for two groups of metrics:
- New (monthly) metrics: `new_stars`, `new_forks`, `new_commits`, `new_prs`, `active_contributors`
- Cumulative metrics: `cumulative_stars`, `cumulative_forks`, `cumulative_commits`, `cumulative_prs`, `cumulative_contributors`

### Scripts and run order
1. `1-process-cumulative-metrics/process-cumulative-metrics.py`
    - Compute the cumulative value of each monthly metric per repository (running sum ordered by month).
2. `3-match-diff-diff/match-parallel-trend-assumption-v2.ipynb`
    - Match each treatment repository to the best control repository using cosine similarity and Euclidean distance on its metric values in the 6 months before the HN submission month (month 0).
    - Check the parallel trend assumption (trend plots and pre-trend slope tests).
    - Build the aligned panels from month -6 to month +6, with a `pair_id` linking each treatment-control pair, saved as `aligned_did_<metric>.csv`.
    - Export the parallel trend figures used in the paper.
3. `3-match-diff-diff/perform-DiD.ipynb`
    - Run the standard and lagged DiD regressions on the aligned panels.
4. `3-match-diff-diff/perform-DiD-eval.ipynb`
    - Run the evaluation: two-way fixed effects DiD (`linearmodels` `PanelOLS`), dynamic (event-study) effects with a Wald test on the pre-trend, and placebo tests at earlier fake treatment dates. The event-study pre-trend test uses the new metrics only; the cumulative metrics are exploratory.

### Required datasets
The notebooks read from `dataset/` (not included in the repository):
- `hn-stories-gh-ai-metrics-[6months-before-after-hn]-cumulative-v2.csv`, `hn-stories-gh-ai-metadata-[6months-before-after-hn]-v2.csv`: Treatment repository metrics and metadata.
- `nonhn-gh-ai-metrics-[2147].csv`, `nonhn-gh-ai-metadata-[2147].csv`, `nonhn-gh-ai-metrics-cumulative.csv`: Control repository metrics and metadata (AI repositories not submitted to HN, selected with [`filter-nonhn-gh-ai/`](../data-collection/2-gh-metrics/filter-nonhn-gh-ai/) in data collection).

## RQ5b - Validation of the Matching
Folder: [`5b-validation/`](5b-validation/)

- `2-analyze_match_unmatch/match-unmatch-analysis.ipynb` (and its `.py` export): Check whether matched repositories are systematically different from the repositories that were available but not matched, separately for the treatment and control sides. Each repository's panel is reduced to one value (sum for new metrics, max for cumulative metrics). Produces box and violin plots, ECDFs, a love plot of standardized mean differences, `balance_table.csv`, and descriptive statistics. It also cross-checks the number of matched pairs per metric.
- `4-custom-matched-control-dataset-tctc/custom-matched-control-dataset.ipynb`: For each `matched_control_<metric>.csv`, drop the snapshot metric columns and add the treatment (`t-6` to `t-1`) and control (`c-6` to `c-1`) values for the 6 months before the treatment's HN submission month. Months outside the panel are left blank rather than set to 0. Also generates summary statistics for `t-1` and `c-1`.
