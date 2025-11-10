{{ config(materialized='view') }}

/*
    Staging Model: Clean sales transaction data
    
    Learning Objectives:
    - Parse datetime fields
    - Extract date parts for analysis
    - Calculate profit margins
*/

SELECT
    sale_id,
    store_id,
    product_id,
    
    -- Parse datetime
    CAST(sale_datetime AS TIMESTAMP) AS sale_timestamp,
    DATE(sale_datetime) AS sale_date,
    HOUR(sale_datetime) AS sale_hour,
    
    -- Categorize time of day
    CASE
        WHEN HOUR(sale_datetime) BETWEEN 6 AND 10 THEN 'Morning'
        WHEN HOUR(sale_datetime) BETWEEN 11 AND 14 THEN 'Lunch'
        WHEN HOUR(sale_datetime) BETWEEN 15 AND 17 THEN 'Afternoon'
        ELSE 'Evening'
    END AS time_period,
    
    quantity,
    unit_price,
    total_amount,
    payment_method,
    
    -- Add processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('cafe_chain', 'raw_sales') }}

WHERE sale_id IS NOT NULL
  AND total_amount > 0