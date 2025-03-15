SELECT
  c.`id` AS comment_id,
  c.`by` AS commenter,
  c.`text` AS comment_text,
  c.`timestamp` AS comment_time,
  c.`parent` AS parent_id,
  s.`id` AS story_id,
  s.`title` AS story_title
FROM
  `bigquery-public-data.hacker_news.full` c
JOIN (
  SELECT
    `id`,
    `title`
  FROM
    `bigquery-public-data.hacker_news.full`
  WHERE
    `timestamp` BETWEEN TIMESTAMP('2022-05-01') AND TIMESTAMP('2022-05-30')
    AND NOT COALESCE(`dead`, FALSE)
    AND NOT COALESCE(`deleted`, FALSE)
    AND `title` IS NOT NULL
    AND `type` = 'story'
    AND COALESCE(`score`, 0) > 0
    AND LENGTH(TRIM(`title`)) > 0
    AND `by` IS NOT NULL
) s
ON c.`parent` = s.`id`
WHERE
  c.`type` = 'comment'
  AND NOT COALESCE(c.`dead`, FALSE)
  AND NOT COALESCE(c.`deleted`, FALSE)
  AND c.`text` IS NOT NULL
  AND LENGTH(TRIM(c.`text`)) > 0;