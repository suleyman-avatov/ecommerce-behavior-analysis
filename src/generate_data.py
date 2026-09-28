import numpy as np
import pandas as pd
import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

RAW_DATA_PATH = 'data/raw/ecommerce_user_behavior_8000.csv'
CLEAN_DATA_PATH = 'data/processed/ecommerce_clean.csv'

FORCE_RECREATE = False 

def check_and_load():
    """
    Проверяет, нужно ли пересоздавать очищенный датасет.
    Возвращает DataFrame и статус (загружен из кэша или создан заново).
    """
    if FORCE_RECREATE or not os.path.exists(CLEAN_DATA_PATH):
        return None, "create"
    
    raw_mtime = os.path.getmtime(RAW_DATA_PATH)
    clean_mtime = os.path.getmtime(CLEAN_DATA_PATH)
    
    if raw_mtime > clean_mtime:
        print(" Исходный файл изменен. Требуется повторная очистка.")
        return None, "create"
        
    print(f" Загрузка готового очищенного датасета из '{CLEAN_DATA_PATH}'...")
    df = pd.read_csv(CLEAN_DATA_PATH)
    return df, "load"

def process_raw_data():
    """
    Основная логика очистки данных.
    """
    print(f" Начало обработки сырых данных из '{RAW_DATA_PATH}'...")
    
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Ошибка: Исходный файл {RAW_DATA_PATH} не найден!")

    df = pd.read_csv(RAW_DATA_PATH)
    print(f" Загружено: {df.shape[0]} строк, {df.shape[1]} столбцов")

    int_cols = ['user_id', 'pages_viewed', 'previous_purchases', 'cart_items',
                'discount_seen', 'ad_clicked', 'returning_user', 'purchase']
    
    for col in int_cols:
        df[col] = df[col].fillna(0).astype(int)

    missing_counts = df.isnull().sum()
    missing_cols = missing_counts[missing_counts > 0]
    
    print("\n--- Анализ пропусков ДО импутации ---")
    if len(missing_cols) > 0:
        for col, count in missing_cols.items():
            pct = (count / len(df)) * 100
            print(f"{col}: {count} пропусков ({pct:.2f}%)")
    else:
        print("Пропусков нет!")
    print("\n🧹 Применение стратегии импутации...")
    
    categorical_cols = ['gender', 'device_type']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
            
    numeric_cols = ['age', 'time_on_site', 'avg_session_time', 'bounce_rate']
    for col in numeric_cols:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"   - Колонка '{col}' заполнена медианой: {median_val:.2f}")

    final_missing = df.isnull().sum().sum()
    print(f"\n Пропусков ПОСЛЕ очистки: {final_missing}")
    
    if final_missing > 0:
        print("ВНИМАНИЕ: Некоторые пропуски остались! Проверьте логику выше.")
        print(df[df.isnull().any(axis=1)].head())

    os.makedirs(os.path.dirname(CLEAN_DATA_PATH), exist_ok=True)
    
    df.to_csv(CLEAN_DATA_PATH, index=False, encoding='utf-8')
    print(f" Очищенный датасет сохранен в '{CLEAN_DATA_PATH}'")
    
    return df

if __name__ == "__main__":
    df_cached, status = check_and_load()
    
    if status == "load":
        df = df_cached
    else:
        df = process_raw_data()

    print("\n" + "="*50)
    print("ИТОГОВАЯ СТАТИСТИКА ПОСЛЕ ОЧИСТКИ")
    print("="*50)
    print(f"Размер: {df.shape[0]} строк × {df.shape[1]} столбцов")
    print("\nРаспределение целевой переменной (purchase):")
    print(df['purchase'].value_counts(normalize=True) * 100)
    print("\nПервые 5 строк:")
    print(df.head())