{{ config(materialized='view') }}

/*
    Staging Model: Household information
    
    Learning Objectives:
    - Categorize by size
    - Calculate per-person metrics
*/

SELECT
    household_id,
    address,
    city,
    state,
    rate_plan,
    sq_footage,
    occupants,
    
    -- Calculate per-person space
    ROUND(sq_footage / occupants, 2) AS sq_ft_per_person,
    
    -- Categorize by size
    CASE
        WHEN sq_footage >= 1500 THEN 'Large'
        WHEN sq_footage >= 1000 THEN 'Medium'
        ELSE 'Small'
    END AS home_size_category,
    
    -- Categorize by occupancy
    CASE
        WHEN occupants >= 4 THEN 'Large Family'
        WHEN occupants >= 2 THEN 'Family'
        ELSE 'Single'
    END AS household_type,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('energy_smart', 'raw_households') }}

WHERE household_id IS NOT NULL