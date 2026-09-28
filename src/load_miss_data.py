import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('ecommerce_user_behavior_8000.csv')
print(df.head()); print(df.describe())

int_cols = ['user_id', 'pages_viewed', 'previous_purchases', 'cart_items',
            'discount_seen', 'ad_clicked', 'returning_user', 'purchase']

for col in int_cols:
    df[col] = df[col].fillna(0).astype(int)

print(f"\nПропусков до очистки: {df.isnull().sum().sum()}")

#Категориальные признаки
df['gender'] = df['gender'].fillna('Unknown')
df['device_type'] = df['device_type'].fillna('Unknown')

#Числовые признаки
df['age'] = df['age'].fillna(df['age'].median())
df['time_on_site'] = df['time_on_site'].fillna(df['time_on_site'].median())
df['avg_session_time'] = df['avg_session_time'].fillna(df['avg_session_time'].median())
df['bounce_rate'] = df['bounce_rate'].fillna(df['bounce_rate'].median())

print(f"\nПропусков после очистки: {df.isnull().sum().sum()}")
print(f"Проверка распределения:\n {df['gender'].value_counts()}")
print(f"Проверка распределения: \n{df['device_type'].value_counts()}")

df.to_csv('ecommerce_clean.csv', index=False, encoding='UTF-8')

