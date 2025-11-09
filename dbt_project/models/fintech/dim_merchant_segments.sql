{{ config(materialized='table') }}

/*
    Dimension Table: Merchant Performance Segments
    
    Learning Objectives:
    - Build analytical segments based on behavior
    - Use window functions and aggregations
    - Categorize merchants for business insights
    - Create reusable dimensional data
*/

WITH merchant_metrics AS (
    SELECT
        t.merchant_id,
        m.merchant_name,
        m.industry,
        m.tier,
        m.tenure_days,
        m.value_segment,
        
        -- Aggregate metrics across all transactions
        COUNT(*) AS total_transaction_count,
        COUNT(CASE WHEN t.is_successful THEN 1 END) AS successful_transaction_count,
        SUM(CASE WHEN t.is_successful THEN t.gross_amount ELSE 0 END) AS total_gmv,
        SUM(CASE WHEN t.is_successful THEN t.processing_fee ELSE 0 END) AS total_revenue_generated,
        AVG(CASE WHEN t.is_successful THEN t.gross_amount END) AS avg_transaction_size,
        
        -- Get date range of activity
        MIN(t.transaction_date) AS first_transaction_date,
        MAX(t.transaction_date) AS last_transaction_date,
        
        -- Count unique customers
        COUNT(DISTINCT t.customer_id) AS unique_customer_count
        
    FROM {{ ref('stg_transactions') }} t
    INNER JOIN {{ ref('stg_merchants') }} m ON t.merchant_id = m.merchant_id
    
    WHERE m.is_active = TRUE
    
    GROUP BY 
        t.merchant_id,
        m.merchant_name,
        m.industry,
        m.tier,
        m.tenure_days,
        m.value_segment
)

SELECT
    *,
    
    -- Calculate success rate
    ROUND(
        (successful_transaction_count::FLOAT / NULLIF(total_transaction_count, 0)) * 100,
        2
    ) AS success_rate_pct,
    
    -- Calculate days active
    DATE_DIFF('day', first_transaction_date, last_transaction_date) + 1 AS days_with_activity,
    
    -- Categorize merchants by volume
    CASE
        WHEN total_revenue_generated >= 500 THEN 'High Volume'
        WHEN total_revenue_generated >= 100 THEN 'Medium Volume'
        ELSE 'Low Volume'
    END AS volume_category,
    
    -- Categorize by customer base
    CASE
        WHEN unique_customer_count >= 10 THEN 'Large Customer Base'
        WHEN unique_customer_count >= 5 THEN 'Medium Customer Base'
        ELSE 'Small Customer Base'
    END AS customer_base_size,
    
    -- Flag for key accounts (high revenue + high success rate)
    CASE
        WHEN total_revenue_generated >= 300 
         AND (successful_transaction_count::FLOAT / NULLIF(total_transaction_count, 0)) >= 0.90 
        THEN TRUE
        ELSE FALSE
    END AS is_key_account,
    
    -- Processing metadata
    CURRENT_TIMESTAMP AS calculated_at
    
FROM merchant_metrics

ORDER BY total_revenue_generated DESC
