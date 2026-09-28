DROP TABLE IF EXISTS mart_conversion_rates;

CREATE TABLE mart_conversion_rates AS
SELECT
    device_type,
    gender,
    
    CASE
        WHEN age BETWEEN 18 AND 25 THEN '18-25'
        WHEN age BETWEEN 26 AND 35 THEN '26-35'
        WHEN age BETWEEN 36 AND 45 THEN '36-45'
        WHEN age BETWEEN 46 AND 55 THEN '46-55'
        ELSE '56+'
    END AS age_group,

    COUNT(*) AS total_users,
    SUM(purchase) AS converted_users,
    
    ROUND(AVG(purchase) * 100.0, 2) AS conversion_rate_pct,
    ROUND(AVG(time_on_site), 2) AS avg_time_on_site,
    ROUND(AVG(pages_viewed), 2) AS avg_pages_viewed,
    ROUND(AVG(cart_items), 2) AS avg_cart_size,
    ROUND(AVG(bounce_rate), 2) AS avg_bounce_rate

FROM stg_ecommerce_users
GROUP BY 
    device_type, 
    gender, 
    age_group;