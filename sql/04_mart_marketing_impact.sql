DROP TABLE IF EXISTS mart_marketing_impact;

CREATE TABLE mart_marketing_impact AS
SELECT
    CASE 
        WHEN discount_seen = 1 AND ad_clicked = 1 THEN 'Both Touchpoints'
        WHEN discount_seen = 1 AND ad_clicked = 0 THEN 'Discount Only'
        WHEN discount_seen = 0 AND ad_clicked = 1 THEN 'Ad Only'
        ELSE 'No Marketing'
    END AS marketing_channel,

    COUNT(*) AS users,
    SUM(purchase) AS buyers,
    ROUND(AVG(purchase) * 100.0, 2) AS conversion_rate_pct,
    ROUND(AVG(cart_items), 2) AS avg_cart_size,
    ROUND(AVG(time_on_site), 2) AS avg_engagement_time

FROM stg_ecommerce_users
GROUP BY marketing_channel;