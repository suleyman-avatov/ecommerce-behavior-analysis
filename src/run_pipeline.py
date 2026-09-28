import sqlite3
import os

def create_marts(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    mart_files = [
        'sql/02_mart_user_segments.sql',
        'sql/03_mart_conversion_rates.sql'
    ]
    
    print("Создание витрин данных (Marts)...")
    
    for file_path in mart_files:
        if not os.path.exists(file_path):
            print(f" Файл {file_path} не найден. Пропуск.")
            continue
            
        print(f" Выполняю: {os.path.basename(file_path)}...", end=" ")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            cursor.executescript(sql_script)
            conn.commit()
            print(" Готово")
            
        except Exception as e:
            print(f"\n Ошибка: {e}")
            conn.rollback()
            break 

    conn.close()
    print("🔒 Соединение закрыто.")

if __name__ == "__main__":
    DB_FILE = 'data/ecommerce_portfolio.db'
    create_marts(DB_FILE)