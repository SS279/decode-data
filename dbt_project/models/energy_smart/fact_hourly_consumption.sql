{{ config(materialized='table') }}

/*
    Fact Table: Hourly Energy Consumption with Costs
    
    Learning Objectives:
    - Join multiple sources
    - Calculate dynamic costs based on conditions
    - Time-series aggregation
*/

SELECT
    r.reading_id,
    r.reading_timestamp,
    r.reading_date,
    r.reading_hour,
    r.time_of_day,
    
    r.household_id,
    h.address,
    h.rate_plan,
    h.sq_footage,
    h.occupants,
    h.household_type,
    
    r.kwh_consumed,
    r.temperature_f,
    r.is_peak_hour,
    
    -- Calculate cost based on rate plan and peak hour
    CASE
        WHEN r.is_peak_hour THEN r.kwh_consumed * rp.peak_rate
        ELSE r.kwh_consumed * rp.off_peak_rate
    END AS cost_dollars,
    
    -- Calculate per-person consumption
    ROUND(r.kwh_consumed / h.occupants, 3) AS kwh_per_person,
    
    -- Calculate per-sqft consumption
    ROUND(r.kwh_consumed / h.sq_footage, 4) AS kwh_per_sqft,
    
    -- Categorize consumption level
    CASE
        WHEN r.kwh_consumed >= 3.0 THEN 'High'
        WHEN r.kwh_consumed >= 1.5 THEN 'Medium'
        ELSE 'Low'
    END AS consumption_level,
    
    -- Flag potential anomalies
    CASE
        WHEN r.kwh_consumed > 4.0 THEN TRUE
        ELSE FALSE
    END AS is_anomaly,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at

FROM {{ ref('stg_meter_readings') }} r
INNER JOIN {{ ref('stg_households') }} h ON r.household_id = h.household_id
INNER JOIN {{ ref('stg_rate_plans') }} rp ON h.rate_plan = rp.rate_plan

ORDER BY r.reading_timestamp DESC