{{ config(materialized='view') }}

/*
    Staging Model: Order Data Preparation
    
    Learning Objectives:
    - Work with date fields
    - Create boolean flags
    - Filter data based on conditions
*/

SELECT
    order_id,
    customer_id,
    
    -- Parse dates
    CAST(order_date AS DATE) AS order_date,
    
    amount,
    status,
    
    -- Create useful flags
    CASE 
        WHEN status = 'completed' THEN TRUE 
        ELSE FALSE 
    END AS is_completed,
    
    CASE 
        WHEN status = 'cancelled' THEN TRUE 
        ELSE FALSE 
    END AS is_cancelled,
    
    -- Add processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('hello_dbt', 'raw_orders') }}

WHERE order_id IS NOT NULL