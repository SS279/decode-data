{{ config(materialized='view') }}

/*
    Staging Model: Prepare merchant dimensional data
    
    Learning Objectives:
    - Work with dimensional (lookup) tables
    - Calculate tenure/age from dates
    - Create business categorizations
*/

SELECT
    merchant_id,
    merchant_name,
    industry,
    country,
    
    -- Date fields
    CAST(signup_date AS DATE) AS signup_date,
    
    -- Calculate merchant tenure in days
    DATEDIFF('day', CAST(signup_date AS DATE), CURRENT_DATE) AS tenure_days,
    
    -- Tier information
    tier,
    monthly_fee,
    status,
    
    -- Categorize by pricing tier
    CASE 
        WHEN tier = 'enterprise' THEN 'High Value'
        WHEN tier = 'premium' THEN 'Medium Value'
        ELSE 'Standard Value'
    END AS value_segment,
    
    -- Status flags
    CASE 
        WHEN status = 'active' THEN TRUE 
        ELSE FALSE 
    END AS is_active,
    
    -- Processing metadata
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('fintech', 'raw_merchants') }}

WHERE status IS NOT NULL
