
DROP TABLE IF EXISTS mart_user_segments;

CREATE TABLE mart_user_segments AS
WITH normalized_metrics AS (
    SELECT
        user_id,
        -- Normalizing metrics to 0-1 scale using Min-Max
        (time_on_site - MIN(time_on_site) OVER ()) / 
        NULLIF(MAX(time_on_site) OVER () - MIN(time_on_site) OVER (), 0) AS norm_time,
        
        (pages_viewed - MIN(pages_viewed) OVER ()) / 
        NULLIF(MAX(pages_viewed) OVER () - MIN(pages_viewed) OVER (), 0) AS norm_pages,
        
        (cart_items - MIN(cart_items) OVER ()) / 
        NULLIF(MAX(cart_items) OVER () - MIN(cart_items) OVER (), 0) AS norm_cart,
        
        time_on_site,
        pages_viewed,
        cart_items,
        purchase,
        bounce_rate
    FROM stg_ecommerce_users
),
scored_users AS (
    SELECT
        *,
        -- Weighted Engagement Score
        (norm_time * 0.4 + norm_pages * 0.3 + norm_cart * 0.3) AS engagement_score
    FROM normalized_metrics
)
SELECT
    user_id,
    engagement_score,
    CASE
        WHEN engagement_score >= 0.7 THEN 'Champions'
        WHEN engagement_score >= 0.4 THEN 'Loyal Customers'
        WHEN engagement_score >= 0.25 THEN 'At Risk'
        ELSE 'Lost Cause'
    END AS customer_segment,
    time_on_site,
    pages_viewed,
    cart_items,
    purchase,
    bounce_rate
FROM scored_users;