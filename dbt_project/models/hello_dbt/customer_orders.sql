{{ config(materialized='table') }}

/*
    Fact Table: Customer Order Summary
    
    Learning Objectives:
    - Use ref() to reference other models
    - Perform aggregations with GROUP BY
    - Calculate summary metrics
    - Build a fact table
*/

SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.country,
    c.signup_date,
    
    -- Order metrics
    COUNT(o.order_id) AS total_orders,
    COUNT(CASE WHEN o.is_completed THEN 1 END) AS completed_orders,
    COUNT(CASE WHEN o.is_cancelled THEN 1 END) AS cancelled_orders,
    
    -- Revenue metrics (only completed orders)
    SUM(CASE WHEN o.is_completed THEN o.amount ELSE 0 END) AS total_revenue,
    AVG(CASE WHEN o.is_completed THEN o.amount END) AS avg_order_value,
    
    -- Date metrics
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    
    -- Calculate days since first order
    DATE_DIFF('day', MIN(o.order_date), CURRENT_DATE) AS days_since_first_order,
    
    -- Customer segmentation
    CASE
        WHEN COUNT(o.order_id) >= 3 THEN 'Frequent'
        WHEN COUNT(o.order_id) = 2 THEN 'Regular'
        ELSE 'New'
    END AS customer_segment,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at

FROM {{ ref('stg_customers') }} c
LEFT JOIN {{ ref('stg_orders') }} o ON c.customer_id = o.customer_id

GROUP BY 
    c.customer_id,
    c.full_name,
    c.email,
    c.country,
    c.signup_date

ORDER BY total_revenue DESC