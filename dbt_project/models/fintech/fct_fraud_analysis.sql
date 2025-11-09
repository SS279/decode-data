{{ config(materialized='table') }}

/*
    Fact Table: Fraud and Risk Analysis
    
    Learning Objectives:
    - Join transactional data with fraud signals
    - Calculate risk scores and metrics
    - Identify patterns in failed transactions
    - Build fraud detection reporting
*/

WITH transaction_flags AS (
    SELECT
        t.transaction_id,
        t.transaction_date,
        t.merchant_id,
        t.customer_id,
        t.gross_amount,
        t.payment_method,
        t.status,
        t.country_code,
        t.is_failed,
        
        -- Join with fraud flags
        f.flag_id,
        f.flag_type,
        f.severity,
        f.reviewed,
        f.notes,
        
        -- Flag presence indicator
        CASE WHEN f.flag_id IS NOT NULL THEN TRUE ELSE FALSE END AS has_fraud_flag
        
    FROM {{ ref('stg_transactions') }} t
    LEFT JOIN {{ source('fintech', 'raw_fraud_flags') }} f 
        ON t.transaction_id = f.transaction_id
    
    WHERE t.is_failed = TRUE OR f.flag_id IS NOT NULL
)

SELECT
    transaction_id,
    transaction_date,
    merchant_id,
    customer_id,
    gross_amount,
    payment_method,
    status,
    country_code,
    
    -- Flag information
    has_fraud_flag,
    flag_type,
    severity,
    reviewed,
    notes,
    
    -- Risk categorization
    CASE
        WHEN severity = 'high' THEN 3
        WHEN severity = 'medium' THEN 2
        WHEN severity = 'low' THEN 1
        ELSE 0
    END AS risk_score,
    
    CASE
        WHEN has_fraud_flag AND NOT reviewed THEN TRUE
        ELSE FALSE
    END AS needs_review,
    
    -- Flag type categorization
    CASE
        WHEN flag_type IN ('velocity_check', 'multiple_attempts') THEN 'Behavioral'
        WHEN flag_type IN ('geo_anomaly', 'unusual_amount') THEN 'Pattern Anomaly'
        WHEN flag_type = 'payment_decline' THEN 'Payment Issue'
        ELSE 'Other'
    END AS risk_category,
    
    -- Processing metadata
    CURRENT_TIMESTAMP AS analyzed_at

FROM transaction_flags

ORDER BY 
    CASE 
        WHEN severity = 'high' THEN 1
        WHEN severity = 'medium' THEN 2
        WHEN severity = 'low' THEN 3
        ELSE 4
    END,
    transaction_date DESC
