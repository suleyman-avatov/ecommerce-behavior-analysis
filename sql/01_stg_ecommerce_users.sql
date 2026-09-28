
DROP TABLE IF EXISTS stg_ecommerce_users;

CREATE TABLE stg_ecommerce_users AS
SELECT
    CAST(user_id AS INTEGER) AS user_id,
    CAST(age AS INTEGER) AS age,
    NULLIF(TRIM(gender), '') AS gender,
    NULLIF(TRIM(device_type), '') AS device_type,
    CAST(time_on_site AS REAL) AS time_on_site,
    CAST(pages_viewed AS INTEGER) AS pages_viewed,
    CAST(previous_purchases AS INTEGER) AS previous_purchases,
    CAST(cart_items AS INTEGER) AS cart_items,
    CAST(discount_seen AS INTEGER) AS discount_seen,
    CAST(ad_clicked AS INTEGER) AS ad_clicked,
    CAST(returning_user AS INTEGER) AS returning_user,
    CAST(avg_session_time AS REAL) AS avg_session_time,
    CAST(bounce_rate AS REAL) AS bounce_rate,
    CAST(purchase AS INTEGER) AS purchase
FROM ecommerce_clean
WHERE user_id IS NOT NULL;

CREATE INDEX idx_stg_device ON stg_ecommerce_users(device_type);
CREATE INDEX idx_stg_gender ON stg_ecommerce_users(gender);
CREATE INDEX idx_stg_purchase ON stg_ecommerce_users(purchase);
CREATE INDEX idx_stg_discount ON stg_ecommerce_users(discount_seen);