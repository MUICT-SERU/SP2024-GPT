-- [unique-repo-urls] script to retrieve metadata for repositories in the hn-stories-gh-[unique-repo-urls] table
-- Joining with GitHub metadata tables in the public 'githubarchive' dataset

WITH repo_list AS (
  SELECT DISTINCT
    owner,
    repo_name,
    repo_full_name
  FROM
    `your-project.hn-stories-gh-[unique-repo-urls]`
  WHERE
    repo_full_name IS NOT NULL
)

SELECT
  r.repo_full_name,
  r.owner,
  r.repo_name,
  MIN(gh.created_at) AS repo_creation_date,
  COUNT(DISTINCT gh.actor.id) AS contributor_count,
  COUNT(DISTINCT IF(gh.type = 'PushEvent', gh.id, NULL)) AS push_count,
  COUNT(DISTINCT IF(gh.type = 'WatchEvent', gh.id, NULL)) AS star_count,
  COUNT(DISTINCT IF(gh.type = 'ForkEvent', gh.id, NULL)) AS fork_count
FROM
  repo_list r
LEFT JOIN
  `githubarchive.month.*` gh
ON
  gh.repo.name = r.repo_full_name
GROUP BY
  r.repo_full_name,
  r.owner,
  r.repo_name
ORDER BY
  repo_creation_date