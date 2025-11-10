{{ config(materialized='view') }}

/*
    Staging Model: Energy rate plans
    
    Learning Objectives:
    - Calculate rate differentials
*/

SELECT
    rate_plan,
    off_peak_rate,
    peak_rate,
    description,
    
    -- Calculate differential
    peak_rate - off_peak_rate AS peak_premium,
    
    ROUND(((peak_rate - off_peak_rate) / off_peak_rate) * 100, 2) AS premium_pct,
    
    -- Categorize plan type
    CASE
        WHEN peak_rate = off_peak_rate THEN 'Flat Rate'
        ELSE 'Time-of-Use'
    END AS plan_type,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('energy_smart', 'raw_rate_plans') }}

WHERE rate_plan IS NOT NULL