import pandas as pd
import sqlite3
import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def load_and_process_raw_data(csv_path, db_path, table_name='ecommerce_raw'):
    """
    Загружает очищенный CSV в SQLite во временную/сырую таблицу.
    Эта таблица будет использоваться SQL-скриптом Staging для трансформации.
    """
    if not os.path.exists(csv_path):
        print(f" Ошибка: Файл {csv_path} не найден!")
        return False

    print(f"Загрузка данных из {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    conn = sqlite3.connect(db_path)

    df.to_sql(table_name, con=conn, if_exists='replace', index=False)
    
    rows_loaded = len(df)
    conn.close()
    
    print(f"Успешно загружено {rows_loaded} строк в таблицу '{table_name}'.")
    return True

def execute_sql_scripts(db_path, sql_dir='sql'):
    """
    Выполняет SQL-скрипты по порядку: сначала Staging, потом Marts.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql_files = [
        os.path.join(sql_dir, '01_stg_ecommerce_users.sql'),
        os.path.join(sql_dir, '02_mart_user_segments.sql'),
        os.path.join(sql_dir, '03_mart_conversion_rates.sql'),
        os.path.join(sql_dir, '04_mart_marketing_impact.sql')
    ]

    print("\n Начало выполнения SQL-скриптов...")
    
    for file_path in sql_files:
        if not os.path.exists(file_path):
            print(f"Пропуск: Файл {file_path} не найден.")
            continue
            
        print(f"Выполняю: {os.path.basename(file_path)}...", end=" ")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            cursor.executescript(script_content)
            conn.commit()
            print("✅ OK")
            
        except Exception as e:
            print(f"\n   ❌ ОШИБКА при выполнении {file_path}: {e}")
            conn.rollback()
            break
            
    conn.close()
    print("🔒 Соединение с базой закрыто.")

if __name__ == "__main__":
    print("ЗАПУСК АНАЛИТИЧЕСКОГО ПАЙПЛАЙНА")
    
    CSV_FILE = 'data/ecommerce_clean.csv'      
    DB_FILE = 'data/ecommerce_portfolio.db'     
    RAW_TABLE_NAME = 'ecommerce_raw_staging'  
    
    success = load_and_process_raw_data(CSV_FILE, DB_FILE, RAW_TABLE_NAME)
    
    if success:
        execute_sql_scripts(DB_FILE)
        
        print("\n" + "="*50)
        print("PIPELINE УСПЕШНО ЗАВЕРШЕН!")
        print("="*50)
        print("Теперь можно подключать Power BI или Streamlit к базе:", DB_FILE)
    else:
        print(" Pipeline остановлен из-за ошибки загрузки данных.")