# ---- 0. Setup ----
# install.packages(c("fixest", "dplyr"))
# install.packages("devtools"); devtools::install_github("jonathandroth/pretrends")

library(fixest)
library(pretrends)
library(dplyr)

# ---- 1. Paths and metric definitions (mirrors your Python variables) ----
aligned_dir <- "aligned_did_outputs_new"   # <-- same folder your Python script reads from

monthly_metrics <- c("new_stars", "new_forks", "new_commits", "new_prs", "active_contributors")

ref_period <- -1

# ---- 2. Loader for MONTHLY (flow) metrics — no transformation needed ----
load_monthly <- function(metric) {
  file_path <- file.path(aligned_dir, paste0("aligned_did_", metric, ".csv"))
  df <- read.csv(file_path, stringsAsFactors = FALSE)
  
  if (nrow(df) == 0) {
    message(sprintf("[!] Skipping empty file: %s", file_path))
    return(NULL)
  }
  
  df$month             <- as.Date(df$month)
  df$hn_submission_date <- as.Date(df$hn_submission_date)
  df$treatment    <- as.integer(df$repo_type == "treatment")
  df$post         <- as.integer(df$post_treatment)
  df$did          <- df$treatment * df$post
  df$rel_month_cat <- as.integer(df$relative_month)
  
  df
}

# ---- 3. Loader for CUMULATIVE metrics — builds the running sum per repo ----
# Your schema only ships cumulative_stars / cumulative_forks pre-built;
# for commits/prs/active_contributors we cumsum the monthly ("new_*") column ourselves,
# same as you did in Python, grouped by repo and ordered by relative_month.
load_cumulative <- function(metric) {
  # source_metric is the underlying monthly column this cumulative version is built from
  source_metric <- switch(metric,
                          cumulative_stars   = "new_stars",
                          cumulative_forks   = "new_forks",
                          cumulative_commits = "new_commits",
                          cumulative_prs     = "new_prs",
                          cumulative_ve_contributors = "active_contributors",
                          stop("Unrecognized cumulative metric: ", metric)
  )
  
  df <- load_monthly(source_metric)  # reuses the same aligned_did_<source>.csv file
  if (is.null(df)) return(NULL)
  
  df <- df %>%
    arrange(repo_full_name, relative_month) %>%
    group_by(repo_full_name) %>%
    mutate(!!metric := cumsum(.data[[source_metric]])) %>%
    ungroup() %>%
    as.data.frame()
  
  df
}

# ---- 4. Event study + pretrends power check, for a data.frame already prepped above ----
run_pretrends <- function(df, outcome_col, cluster_var = "repo_full_name") {
  
  form <- as.formula(paste0(
    outcome_col, " ~ i(rel_month_cat, ref = ", ref_period, ") + ",
    "i(rel_month_cat, treatment, ref = ", ref_period, ") + treatment"
  ))
  
  model <- feols(form, data = df, cluster = as.formula(paste0("~", cluster_var)))
  
  all_coefs <- coef(model)
  all_vcov  <- vcov(model)
  
  interaction_idx <- grepl("rel_month_cat.*:treatment", names(all_coefs))
  beta  <- all_coefs[interaction_idx]
  sigma <- all_vcov[interaction_idx, interaction_idx]
  
  tVec <- as.numeric(gsub(".*rel_month_cat::(-?[0-9]+):treatment.*", "\\1", names(beta)))
  
  pre_idx   <- tVec < ref_period
  beta_pre  <- beta[pre_idx]
  sigma_pre <- sigma[pre_idx, pre_idx]
  tVec_pre  <- tVec[pre_idx]
  
  slope50 <- slope_for_power(sigma = sigma_pre, targetPower = 0.5,
                             tVec = tVec_pre, referencePeriod = ref_period)
  slope80 <- slope_for_power(sigma = sigma_pre, targetPower = 0.8,
                             tVec = tVec_pre, referencePeriod = ref_period)
  
  power_check <- pretrends(betahat = beta_pre, sigma = sigma_pre, tVec = tVec_pre,
                           referencePeriod = ref_period,
                           deltatrue = slope50 * (tVec_pre - ref_period))
  
  list(metric = outcome_col, model = model,
       slope50 = slope50, slope80 = slope80,
       power_table = power_check$df_power,
       event_plot = power_check$event_plot)
}

# ---- 5. Run for monthly metrics ----
monthly_results <- list()
for (metric in monthly_metrics) {
  df <- load_monthly(metric)
  if (is.null(df)) next
  monthly_results[[metric]] <- run_pretrends(df, outcome_col = metric)
}

# ---- 6. Run for cumulative metrics ----
cumulative_metrics <- c("cumulative_stars", "cumulative_forks", "cumulative_commits",
                        "cumulative_prs", "cumulative_ve_contributors")

cumulative_results <- list()
for (metric in cumulative_metrics) {
  df <- load_cumulative(metric)
  if (is.null(df)) next
  cumulative_results[[metric]] <- run_pretrends(df, outcome_col = metric)
}

# ---- 7. Inspect results ----
for (m in names(monthly_results)) {
  cat("\n====", m, "(monthly) ====\n")
  cat("Slope detected 50% of the time:", monthly_results[[m]]$slope50, "\n")
  cat("Slope detected 80% of the time:", monthly_results[[m]]$slope80, "\n")
  print(monthly_results[[m]]$power_table)
}

for (m in names(cumulative_results)) {
  cat("\n====", m, "(cumulative) ====\n")
  cat("Slope detected 50% of the time:", cumulative_results[[m]]$slope50, "\n")
  cat("Slope detected 80% of the time:", cumulative_results[[m]]$slope80, "\n")
  print(cumulative_results[[m]]$power_table)
}