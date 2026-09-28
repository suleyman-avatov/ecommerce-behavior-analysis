import pandas as pd
import sqlite3
import os

# Пути к файлам
DB_FILE = 'ecommerce_portfolio.db'
OUTPUT_DIR = 'sql_results'

# Создаем папку для результатов, если её нет
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Подключение к базе
conn = sqlite3.connect(DB_FILE)

print(" Выполнение аналитических запросов...\n")

# ==========================================
# ЗАПРОС 1: RFM-подобная сегментация пользователей
# Цель: Разделить пользователей на группы по вовлеченности
# Навык: CTE (WITH), NTILE, CASE WHEN
# ==========================================
query_rfm = """
WITH user_metrics AS (
    SELECT 
        user_id,
        time_on_site,
        pages_viewed,
        cart_items,
        purchase,
        -- Ранжируем пользователей по квартилям (4 группы)
        NTILE(4) OVER (ORDER BY time_on_site DESC) as t_score,
        NTILE(4) OVER (ORDER BY pages_viewed DESC) as p_score,
        NTILE(4) OVER (ORDER BY cart_items DESC) as c_score
    FROM ecommerce_users
)
SELECT 
    user_id,
    t_score,
    p_score,
    c_score,
    -- Простая логика сегментации: сумма баллов определяет ценность
    (t_score + p_score + c_score) as engagement_score,
    CASE 
        WHEN (t_score + p_score + c_score) >= 9 THEN 'Champions'
        WHEN (t_score + p_score + c_score) >= 6 THEN 'Loyal Customers'
        WHEN (t_score + p_score + c_score) >= 4 THEN 'Potential Loyalists'
        ELSE 'At Risk / New'
    END as segment_name,
    purchase
FROM user_metrics;
"""

# Запускаем запрос и сохраняем результат
try:
    df_rfm = pd.read_sql(query_rfm, conn)
    df_rfm.to_csv(f'{OUTPUT_DIR}/01_user_segments.csv', index=False)
    print(f" [RFM] Сохранено {len(df_rfm)} записей в 01_user_segments.csv")
    print(df_rfm['segment_name'].value_counts()) # Краткий обзор
except Exception as e:
    print(f" Ошибка в RFM запросе: {e}")


# ==========================================
# ЗАПРОС 2: Конверсия и поведение по устройствам/полу
# Цель: Найти инсайты для маркетинга
# Навык: GROUP BY, Агрегатные функции, ROUND
# ==========================================
query_conversion = """
SELECT 
    device_type,
    gender,
    COUNT(*) as total_users,
    SUM(purchase) as converted_users,
    ROUND(AVG(purchase) * 100, 2) as conversion_rate_pct,
    ROUND(AVG(time_on_site), 2) as avg_time_on_site,
    ROUND(AVG(cart_items), 2) as avg_cart_size,
    ROUND(AVG(bounce_rate), 2) as avg_bounce_rate
FROM ecommerce_users
GROUP BY device_type, gender
HAVING COUNT(*) > 50 -- Фильтруем маленькие группы для статистической значимости
ORDER BY conversion_rate_pct DESC;
"""

try:
    df_conv = pd.read_sql(query_conversion, conn)
    df_conv.to_csv(f'{OUTPUT_DIR}/02_conversion_by_device_gender.csv', index=False)
    print(f"\n[Конверсия] Сохранено {len(df_conv)} групп в 02_conversion_by_device_gender.csv")
except Exception as e:
    print(f"Ошибка в запросе конверсии: {e}")


# ==========================================
# ЗАПРОС 3: Топ пользователей с высокой корзиной, но без покупки (Risk Group)
# Цель: Выявить группу для ретаргетинга (кто почти купил)
# Навык: WHERE фильтры, ORDER BY, LIMIT
# ==========================================
query_high_intent_no_buy = """
SELECT 
    user_id,
    age,
    gender,
    device_type,
    time_on_site,
    cart_items,
    bounce_rate,
    discount_seen,
    ad_clicked
FROM ecommerce_users
WHERE purchase = 0          -- Не купили
  AND cart_items >= 5       -- Но корзина большая
  AND time_on_site > 10     -- И долго сидели (высокая вовлеченность)
ORDER BY cart_items DESC, time_on_site DESC
LIMIT 20;
"""

try:
    df_risk = pd.read_sql(query_high_intent_no_buy, conn)
    df_risk.to_csv(f'{OUTPUT_DIR}/03_high_intent_non_buyers.csv', index=False)
    print(f"\n[Риск группа] Найдено {len(df_risk)} пользователей для ретаргетинга")
except Exception as e:
    print(f" Ошибка в поиске риск-группы: {e}")


# ==========================================
# ЗАПРОС 4: Статистика влияния скидки (Discount Impact)
# Цель: Показать эффект A/B теста (если бы он был) или корреляцию
# Навык: CASE WHEN, AVG, Сравнение групп
# ==========================================
query_discount_impact = """
SELECT 
    CASE 
        WHEN discount_seen = 1 THEN 'With Discount' 
        ELSE 'No Discount' 
    END as group_name,
    COUNT(*) as users,
    ROUND(AVG(cart_items), 2) as avg_cart_items,
    ROUND(AVG(purchase) * 100, 2) as conversion_pct,
    ROUND(AVG(time_on_site), 2) as avg_time_on_site,
    ROUND(AVG(bounce_rate), 2) as avg_bounce_rate
FROM ecommerce_users
GROUP BY discount_seen;
"""

try:
    df_disc = pd.read_sql(query_discount_impact, conn)
    df_disc.to_csv(f'{OUTPUT_DIR}/04_discount_impact.csv', index=False)
    print(f"\n[Скидки] Данные сохранены в 04_discount_impact.csv")
    print(df_disc)
except Exception as e:
    print(f" Ошибка в анализе скидок: {e}")


# ==========================================
# ЗАПРОС 5: Возрастные когорты и средний чек (корзина)
# Цель: Демографический анализ
# Навык: CASE WHEN для биннинга возраста
# ==========================================
query_age_groups = """
SELECT 
    CASE 
        WHEN age BETWEEN 18 AND 24 THEN 'Gen Z (18-24)'
        WHEN age BETWEEN 25 AND 34 THEN 'Millennials (25-34)'
        WHEN age BETWEEN 35 AND 44 THEN 'Gen X Early (35-44)'
        WHEN age BETWEEN 45 AND 54 THEN 'Gen X Late (45-54)'
        WHEN age >= 55 THEN 'Boomers/Silent (55+)'
        ELSE 'Unknown'
    END as age_group,
    COUNT(*) as users,
    ROUND(AVG(cart_items), 2) as avg_cart_size,
    ROUND(AVG(time_on_site), 2) as avg_engagement_time,
    ROUND(SUM(purchase) * 100.0 / COUNT(*), 2) as conversion_rate
FROM ecommerce_users
WHERE age IS NOT NULL
GROUP BY age_group
ORDER BY MIN(age); -- Сортировка по реальному возрасту, а не алфавиту
"""

try:
    df_age = pd.read_sql(query_age_groups, conn)
    df_age.to_csv(f'{OUTPUT_DIR}/05_age_demographics.csv', index=False)
    print(f"\n [Демография] Данные сохранены в 05_age_demographics.csv")
except Exception as e:
    print(f" Ошибка в демографическом анализе: {e}")


conn.close()
print("\n Все SQL-запросы выполнены. Результаты лежат в папке 'sql_results'.")