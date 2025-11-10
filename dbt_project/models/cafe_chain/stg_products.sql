{{ config(materialized='view') }}

/*
    Staging Model: Product information
    
    Learning Objectives:
    - Calculate profit margins
    - Categorize products
*/

SELECT
    product_id,
    product_name,
    category,
    cost_price,
    selling_price,
    
    -- Calculate margins
    selling_price - cost_price AS profit_per_unit,
    ROUND(((selling_price - cost_price) / selling_price) * 100, 2) AS profit_margin_pct,
    
    -- Categorize by price
    CASE
        WHEN selling_price >= 6.00 THEN 'Premium'
        WHEN selling_price >= 4.00 THEN 'Standard'
        ELSE 'Budget'
    END AS price_tier,
    
    -- Processing timestamp
    CURRENT_TIMESTAMP AS processed_at

FROM {{ source('cafe_chain', 'raw_products') }}

WHERE product_id IS NOT NULL