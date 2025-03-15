-- Collect monthly metrics for all repositories from 2022-05-01 to 2025-01-31

-- Collect monthly metrics for all repositories
CREATE OR REPLACE TABLE `your_dataset.hn-stories-gh-monthly-metrics` AS
WITH
-- Get star events (WatchEvent in GitHub API)
star_events AS (
  SELECT
    repo.name AS repo_full_name,
    FORMAT_TIMESTAMP('%Y-%m', created_at) AS month,
    COUNT(*) AS new_stars
  FROM `githubarchive.day.2*`
  WHERE
    type = 'WatchEvent'
    AND repo.name IN (SELECT repo_full_name FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`)
    AND _TABLE_SUFFIX BETWEEN '0220501' AND '0250131'
  GROUP BY repo_full_name, month
),

-- Get fork events
fork_events AS (
  SELECT
    repo.name AS repo_full_name,
    FORMAT_TIMESTAMP('%Y-%m', created_at) AS month,
    COUNT(*) AS new_forks
  FROM `githubarchive.day.2*`
  WHERE
    type = 'ForkEvent'
    AND repo.name IN (SELECT repo_full_name FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`)
    AND _TABLE_SUFFIX BETWEEN '0220501' AND '0220601'
  GROUP BY repo_full_name, month
),

-- Get commit events
commit_events AS (
  SELECT
    repo.name AS repo_full_name,
    FORMAT_TIMESTAMP('%Y-%m', created_at) AS month,
    COUNT(*) AS commit_count
  FROM `githubarchive.day.2*`
  WHERE
    type = 'PushEvent'
    AND repo.name IN (SELECT repo_full_name FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`)
    AND _TABLE_SUFFIX BETWEEN '0220501' AND '0250131'
  GROUP BY repo_full_name, month
),

-- Get PR events
pr_events AS (
  SELECT
    repo.name AS repo_full_name,
    FORMAT_TIMESTAMP('%Y-%m', created_at) AS month,
    COUNT(*) AS new_prs
  FROM `githubarchive.day.2*`
  WHERE
    type = 'PullRequestEvent'
    AND repo.name IN (SELECT repo_full_name FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`)
    AND _TABLE_SUFFIX BETWEEN '0220501' AND '0250131'
  GROUP BY repo_full_name, month
),

-- Get contributor counts
contributor_events AS (
  SELECT
    repo.name AS repo_full_name,
    FORMAT_TIMESTAMP('%Y-%m', created_at) AS month,
    COUNT(DISTINCT actor.login) AS active_contributors
  FROM `githubarchive.day.2*`
  WHERE
    type IN ('PushEvent', 'PullRequestEvent')
    AND repo.name IN (SELECT repo_full_name FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`)
    AND _TABLE_SUFFIX BETWEEN '0220501' AND '0250131'
  GROUP BY repo_full_name, month
),

-- Generate all month-repo combinations to ensure we have complete data
all_months AS (
  SELECT month FROM UNNEST(GENERATE_DATE_ARRAY(
    DATE('2022-05-01'),
    DATE('2025-01-31'),
    INTERVAL 1 MONTH
  )) AS month
),

all_repos AS (
  SELECT
    repo_full_name,
    repo_url,
    hn_submission_date,
    hn_score,
    source
  FROM `your_dataset.hn-stories-gh-[unique-repo-urls]`
),

all_combinations AS (
  SELECT
    repo_full_name,
    repo_url,
    FORMAT_DATE('%Y-%m', month) AS month,
    hn_submission_date,
    hn_score,
    source
  FROM all_repos
  CROSS JOIN all_months
)

-- Join all data
SELECT
  ac.repo_full_name,
  ac.repo_url,
  ac.month,
  ac.hn_submission_date,
  ac.source,
  ac.hn_score,
  IFNULL(s.new_stars, 0) AS new_stars,
  IFNULL(f.new_forks, 0) AS new_forks,
  IFNULL(c.commit_count, 0) AS commit_count,
  IFNULL(p.new_prs, 0) AS new_prs,
  IFNULL(u.active_contributors, 0) AS active_contributors,
  -- Add cumulative metrics for DiD analysis
  SUM(IFNULL(s.new_stars, 0)) OVER(
    PARTITION BY ac.repo_full_name
    ORDER BY ac.month
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_stars,
  SUM(IFNULL(f.new_forks, 0)) OVER(
    PARTITION BY ac.repo_full_name
    ORDER BY ac.month
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_forks
FROM all_combinations ac
LEFT JOIN star_events s
  ON ac.repo_full_name = s.repo_full_name AND ac.month = s.month
LEFT JOIN fork_events f
  ON ac.repo_full_name = f.repo_full_name AND ac.month = f.month
LEFT JOIN commit_events c
  ON ac.repo_full_name = c.repo_full_name AND ac.month = c.month
LEFT JOIN pr_events p
  ON ac.repo_full_name = p.repo_full_name AND ac.month = p.month
LEFT JOIN contributor_events u
  ON ac.repo_full_name = u.repo_full_name AND ac.month = u.month
ORDER BY ac.repo_full_name, ac.month;