{{ config(materialized='view') }}

/*
    Staging Model: Customer Data Preparation
    
    Learning Objectives:
    - Understand the staging layer concept
    - Learn basic SELECT transformations
    - Practice column renaming and formatting
*/

SELECT
    customer_id,
    first_name,
    last_name,
    
    -- Concatenate full name
    first_name || ' ' || last_name AS full_name,
    
    email,
    
    -- Parse signup date
    CAST(signup_date AS DATE) AS signup_date,
    
    country,
    
    -- Add processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('hello_dbt', 'raw_customers') }}

-- Filter out any null customer IDs
WHERE customer_id IS NOT NULL