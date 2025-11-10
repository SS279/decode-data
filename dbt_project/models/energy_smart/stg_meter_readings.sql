{{ config(materialized='view') }}

/*
    Staging Model: Clean IoT sensor readings
    
    Learning Objectives:
    - Parse timestamps from IoT devices
    - Handle time-series data
    - Extract temporal features
*/

SELECT
    reading_id,
    meter_id,
    household_id,
    
    -- Parse datetime
    CAST(reading_datetime AS TIMESTAMP) AS reading_timestamp,
    DATE(reading_datetime) AS reading_date,
    HOUR(reading_datetime) AS reading_hour,
    
    -- Categorize time of day
    CASE
        WHEN HOUR(reading_datetime) BETWEEN 0 AND 5 THEN 'Night'
        WHEN HOUR(reading_datetime) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN HOUR(reading_datetime) BETWEEN 12 AND 17 THEN 'Afternoon'
        ELSE 'Evening'
    END AS time_of_day,
    
    kwh_consumed,
    temperature_f,
    is_peak_hour,
    
    -- Add processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('energy_smart', 'raw_meter_readings') }}

WHERE reading_id IS NOT NULL
  AND kwh_consumed >= 0