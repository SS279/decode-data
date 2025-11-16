{{ config(materialized='table') }}

/*
    Fact Table: Daily Revenue and Transaction Metrics
    
    Learning Objectives:
    - Aggregate transaction data by day and merchant
    - Calculate key business metrics (GMV, revenue, success rate)
    - Use dbt ref() function to reference staging models
    - Understand fact table design patterns
*/

WITH daily_stats AS (
    SELECT
        t.transaction_date,
        t.merchant_id,
        m.merchant_name,
        m.industry,
        m.tier,
        m.value_segment,
        
        -- Volume metrics
        COUNT(*) AS total_transactions,
        COUNT(CASE WHEN t.is_successful THEN 1 END) AS successful_transactions,
        COUNT(CASE WHEN t.is_failed THEN 1 END) AS failed_transactions,
        
        -- Revenue metrics (GMV = Gross Merchandise Volume)
        SUM(CASE WHEN t.is_successful THEN t.gross_amount ELSE 0 END) AS daily_gmv,
        SUM(CASE WHEN t.is_successful THEN t.processing_fee ELSE 0 END) AS daily_revenue,
        SUM(CASE WHEN t.is_successful THEN t.net_amount ELSE 0 END) AS daily_net_to_merchant,
        
        -- Average transaction values
        AVG(CASE WHEN t.is_successful THEN t.gross_amount END) AS avg_transaction_value,
        
        -- Payment method breakdown
        COUNT(CASE WHEN t.payment_method = 'credit_card' AND t.is_successful THEN 1 END) AS credit_card_count,
        COUNT(CASE WHEN t.payment_method = 'debit_card' AND t.is_successful THEN 1 END) AS debit_card_count,
        COUNT(CASE WHEN t.payment_method = 'paypal' AND t.is_successful THEN 1 END) AS paypal_count,
        COUNT(CASE WHEN t.payment_method = 'bank_transfer' AND t.is_successful THEN 1 END) AS bank_transfer_count
        
    FROM {{ ref('stg_transactions') }} t
    LEFT JOIN {{ ref('stg_merchants') }} m ON t.merchant_id = m.merchant_id
    
    GROUP BY 
        t.transaction_date,
        t.merchant_id,
        m.merchant_name,
        m.industry,
        m.tier,
        m.value_segment
)

SELECT
    *,
    
    -- Calculate success rate percentage
    ROUND(
        (successful_transactions::FLOAT / NULLIF(total_transactions, 0)) * 100, 
        2
    ) AS success_rate_pct,
    
    -- Calculate revenue per transaction
    ROUND(
        daily_revenue / NULLIF(successful_transactions, 0),
        2
    ) AS revenue_per_transaction,
    
    -- Flag high-value days (more than $1000 in revenue)
    CASE 
        WHEN daily_revenue >= 1000 THEN TRUE 
        ELSE FALSE 
    END AS is_high_value_day,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at
    
FROM daily_stats

ORDER BY transaction_date DESC, daily_revenue DESC
