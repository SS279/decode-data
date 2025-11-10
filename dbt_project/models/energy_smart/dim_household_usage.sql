{{ config(materialized='table') }}

/*
    Dimension Table: Household Usage Patterns
    
    Learning Objectives:
    - Aggregate time-series data
    - Calculate statistics
    - Identify patterns
*/

SELECT
    h.household_id,
    h.address,
    h.city,
    h.rate_plan,
    h.sq_footage,
    h.occupants,
    h.household_type,
    h.home_size_category,
    
    -- Consumption statistics
    COUNT(r.reading_id) AS total_readings,
    SUM(r.kwh_consumed) AS total_kwh_consumed,
    AVG(r.kwh_consumed) AS avg_kwh_per_hour,
    MAX(r.kwh_consumed) AS peak_kwh,
    MIN(r.kwh_consumed) AS min_kwh,
    
    -- Cost statistics
    SUM(CASE WHEN r.is_peak_hour THEN r.kwh_consumed * rp.peak_rate ELSE r.kwh_consumed * rp.off_peak_rate END) AS total_cost,
    AVG(CASE WHEN r.is_peak_hour THEN r.kwh_consumed * rp.peak_rate ELSE r.kwh_consumed * rp.off_peak_rate END) AS avg_hourly_cost,
    
    -- Peak vs off-peak analysis
    SUM(CASE WHEN r.is_peak_hour THEN r.kwh_consumed ELSE 0 END) AS peak_hour_kwh,
    SUM(CASE WHEN NOT r.is_peak_hour THEN r.kwh_consumed ELSE 0 END) AS off_peak_kwh,
    
    ROUND((SUM(CASE WHEN r.is_peak_hour THEN r.kwh_consumed ELSE 0 END) / SUM(r.kwh_consumed)) * 100, 2) AS pct_peak_usage,
    
    -- Time of day breakdown
    AVG(CASE WHEN r.time_of_day = 'Morning' THEN r.kwh_consumed END) AS avg_morning_kwh,
    AVG(CASE WHEN r.time_of_day = 'Afternoon' THEN r.kwh_consumed END) AS avg_afternoon_kwh,
    AVG(CASE WHEN r.time_of_day = 'Evening' THEN r.kwh_consumed END) AS avg_evening_kwh,
    AVG(CASE WHEN r.time_of_day = 'Night' THEN r.kwh_consumed END) AS avg_night_kwh,
    
    -- Per-person and per-sqft metrics
    ROUND(SUM(r.kwh_consumed) / h.occupants, 2) AS total_kwh_per_person,
    ROUND(SUM(r.kwh_consumed) / h.sq_footage, 4) AS total_kwh_per_sqft,
    
    -- Efficiency rating
    CASE
        WHEN SUM(r.kwh_consumed) / h.sq_footage < 0.02 THEN 'Highly Efficient'
        WHEN SUM(r.kwh_consumed) / h.sq_footage < 0.04 THEN 'Efficient'
        WHEN SUM(r.kwh_consumed) / h.sq_footage < 0.06 THEN 'Average'
        ELSE 'Inefficient'
    END AS efficiency_rating,
    
    -- Savings opportunity (for time-of-use customers)
    CASE
        WHEN h.rate_plan = 'Time-of-Use' AND (SUM(CASE WHEN r.is_peak_hour THEN r.kwh_consumed ELSE 0 END) / SUM(r.kwh_consumed)) > 0.40
        THEN 'High Savings Potential'
        WHEN h.rate_plan = 'Time-of-Use' AND (SUM(CASE WHEN r.is_peak_hour THEN r.kwh_consumed ELSE 0 END) / SUM(r.kwh_consumed)) > 0.25
        THEN 'Medium Savings Potential'
        ELSE 'Optimized'
    END AS savings_opportunity,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at

FROM {{ ref('stg_households') }} h
LEFT JOIN {{ ref('stg_meter_readings') }} r ON h.household_id = r.household_id
LEFT JOIN {{ ref('stg_rate_plans') }} rp ON h.rate_plan = rp.rate_plan

GROUP BY 
    h.household_id,
    h.address,
    h.city,
    h.rate_plan,
    h.sq_footage,
    h.occupants,
    h.household_type,
    h.home_size_category,
    rp.peak_rate,
    rp.off_peak_rate

ORDER BY total_kwh_consumed DESC