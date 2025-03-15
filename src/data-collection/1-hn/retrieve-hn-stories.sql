SELECT
  `by`,
  `dead`,
  `id`,
  `score`,
  `text`,
  `time`,
  `timestamp`,
  `title`,
  `type`,
  `url`
FROM
  `bigquery-public-data.hacker_news.full`
WHERE
  `timestamp` BETWEEN TIMESTAMP('2022-05-08') AND TIMESTAMP('2024-05-09')
  AND NOT COALESCE(`dead`, FALSE)
  AND NOT COALESCE(`deleted`, FALSE)
  AND `title` IS NOT NULL
  AND `url` IS NOT NULL
  AND `type` = 'story'
  AND COALESCE(`score`, 0) > 0
  AND LENGTH(TRIM(`title`)) > 0
  AND `by` IS NOT NULL
  ;