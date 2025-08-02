-- Fails if fewer than 50 k joined rows for the target date
\set target_date '''' :env_target_date ''''        -- gets value from psql -v

SELECT COUNT(*) AS joined_rows
  FROM status_with_weather
 WHERE ts::date = :target_date;