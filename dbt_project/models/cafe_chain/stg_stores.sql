{{ config(materialized='view') }}

/*
    Staging Model: Store information
    
    Learning Objectives:
    - Calculate business age
    - Categorize by size
*/

SELECT
    store_id,
    store_name,
    city,
    state,
    
    -- Parse date
    CAST(opened_date AS DATE) AS opened_date,
    
    -- Calculate age
    DATE_DIFF('month', CAST(opened_date AS DATE), CURRENT_DATE) AS months_open,
    
    store_size_sqft,
    monthly_rent,
    
    -- Calculate rent per sqft
    ROUND(monthly_rent / store_size_sqft, 2) AS rent_per_sqft,
    
    -- Categorize by size
    CASE
        WHEN store_size_sqft >= 1400 THEN 'Large'
        WHEN store_size_sqft >= 1100 THEN 'Medium'
        ELSE 'Small'
    END AS store_size_category,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('cafe_chain', 'raw_stores') }}

WHERE store_id IS NOT NULL