{{ config(materialized='table') }}

/*
    Fact Table: Daily Sales by Store
    
    Learning Objectives:
    - Aggregate sales data
    - Calculate multiple metrics
    - Use ref() to join staging models
*/

SELECT
    s.sale_date,
    s.store_id,
    st.store_name,
    st.city,
    
    -- Volume metrics
    COUNT(s.sale_id) AS total_transactions,
    SUM(s.quantity) AS total_items_sold,
    
    -- Revenue metrics
    SUM(s.total_amount) AS daily_revenue,
    AVG(s.total_amount) AS avg_transaction_value,
    
    -- Calculate profit (need to join with products)
    SUM(s.quantity * p.profit_per_unit) AS daily_profit,
    
    -- Time period breakdown
    COUNT(CASE WHEN s.time_period = 'Morning' THEN 1 END) AS morning_transactions,
    COUNT(CASE WHEN s.time_period = 'Lunch' THEN 1 END) AS lunch_transactions,
    COUNT(CASE WHEN s.time_period = 'Afternoon' THEN 1 END) AS afternoon_transactions,
    COUNT(CASE WHEN s.time_period = 'Evening' THEN 1 END) AS evening_transactions,
    
    -- Payment method breakdown
    COUNT(CASE WHEN s.payment_method = 'credit_card' THEN 1 END) AS credit_card_count,
    COUNT(CASE WHEN s.payment_method = 'debit_card' THEN 1 END) AS debit_card_count,
    COUNT(CASE WHEN s.payment_method = 'cash' THEN 1 END) AS cash_count,
    
    -- Peak hour
    MODE(s.sale_hour) AS peak_hour,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at

FROM {{ ref('stg_sales') }} s
INNER JOIN {{ ref('stg_stores') }} st ON s.store_id = st.store_id
INNER JOIN {{ ref('stg_products') }} p ON s.product_id = p.product_id

GROUP BY 
    s.sale_date,
    s.store_id,
    st.store_name,
    st.city

ORDER BY s.sale_date DESC, daily_revenue DESC