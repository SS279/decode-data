{{ config(materialized='view') }}

/*
    Staging Model: Clean and standardize raw transaction data
    
    Learning Objectives:
    - Understand data type casting and formatting
    - Learn to handle timestamps properly
    - Calculate derived fields (net_amount after fees)
    - Filter out incomplete records
*/

SELECT
    transaction_id,
    merchant_id,
    customer_id,
    
    -- Parse timestamp to proper datetime format
    CAST(transaction_date AS TIMESTAMP) AS transaction_timestamp,
    DATE(transaction_date) AS transaction_date,
    
    -- Financial calculations
    amount AS gross_amount,
    processing_fee,
    amount - processing_fee AS net_amount,
    currency,
    
    -- Transaction details
    payment_method,
    status,
    country_code,
    
    -- Status flags for easy filtering
    CASE 
        WHEN status = 'completed' THEN TRUE 
        ELSE FALSE 
    END AS is_successful,
    
    CASE 
        WHEN status = 'failed' THEN TRUE 
        ELSE FALSE 
    END AS is_failed,
    
    -- Add processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('fintech', 'raw_transactions') }}

-- Only include valid transactions with positive amounts
WHERE amount > 0
