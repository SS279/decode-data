{{ config(materialized='table') }}

/*
    Dimension Table: Product Performance Analysis
    
    Learning Objectives:
    - Aggregate by product
    - Calculate performance metrics
    - Rank products
*/

SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.selling_price,
    p.profit_per_unit,
    p.profit_margin_pct,
    p.price_tier,
    
    -- Sales metrics
    COUNT(s.sale_id) AS total_sales_count,
    SUM(s.quantity) AS total_units_sold,
    SUM(s.total_amount) AS total_revenue,
    SUM(s.quantity * p.profit_per_unit) AS total_profit,
    
    -- Average metrics
    AVG(s.quantity) AS avg_quantity_per_sale,
    
    -- Performance indicators
    CASE
        WHEN SUM(s.total_amount) >= 100 THEN 'High Performer'
        WHEN SUM(s.total_amount) >= 50 THEN 'Medium Performer'
        ELSE 'Low Performer'
    END AS performance_tier,
    
    -- Popularity rank
    RANK() OVER (ORDER BY SUM(s.quantity) DESC) AS popularity_rank,
    
    -- Revenue rank
    RANK() OVER (ORDER BY SUM(s.total_amount) DESC) AS revenue_rank,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS calculated_at

FROM {{ ref('stg_products') }} p
LEFT JOIN {{ ref('stg_sales') }} s ON p.product_id = s.product_id

GROUP BY 
    p.product_id,
    p.product_name,
    p.category,
    p.selling_price,
    p.profit_per_unit,
    p.profit_margin_pct,
    p.price_tier

ORDER BY total_revenue DESC