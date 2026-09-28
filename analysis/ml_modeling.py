import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

import sys
import io
import os
from pathlib import Path  

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CURRENT_FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_FILE_DIR.parent

DATA_DIR = PROJECT_ROOT / 'data'
ASSETS_DIR = PROJECT_ROOT / 'assets'

os.makedirs(ASSETS_DIR, exist_ok=True)
INPUT_CSV_PATH = DATA_DIR / 'ecommerce_clean.csv'
OUTPUT_PLOT_PATH = ASSETS_DIR / 'ml_feature_importance.png'
OUTPUT_FEATURE_IMPORTANCE_PATH = DATA_DIR / 'ml_top_feature_engagement.csv'

print(f"Корень проекта: {PROJECT_ROOT}")
print(f"Входной файл: {INPUT_CSV_PATH}")

try:
    df = pd.read_csv(INPUT_CSV_PATH)
except FileNotFoundError:
    print(f" ОШИБКА: Файл не найден по пути {INPUT_CSV_PATH}")
    print("Проверьте структуру папок. Убедитесь, что 'ecommerce_clean.csv' лежит в папке 'data'.")
    sys.exit(1)

threshold_time = df['time_on_site'].quantile(0.6)
threshold_pages = df['pages_viewed'].quantile(0.6)

df['is_high_engagement'] = (
    (df['time_on_site'] > threshold_time) | 
    (df['pages_viewed'] > threshold_pages)
).astype(int)

print(f"Баланс таргета is_high_engagement:\n{df['is_high_engagement'].value_counts(normalize=True)}\n")

features = ['age', 'gender', 'device_type', 'time_on_site', 'pages_viewed',
            'previous_purchases', 'cart_items', 'discount_seen', 'ad_clicked',
            'returning_user', 'avg_session_time', 'bounce_rate']

X = pd.get_dummies(df[features], drop_first=True)
y = df['is_high_engagement']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, 
    stratify=y  
)

unique_classes = np.unique(y_train)
print(f"Классы в обучающей выборке: {unique_classes}")
assert len(unique_classes) == 2, "Ошибка: В обучающей выборке менее 2 классов!"

model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
proba_all = model.predict_proba(X_test)

if proba_all.shape[1] == 2:
    y_prob = proba_all[:, 1]
else:
    y_prob = np.where(model.classes_ == 1, proba_all[:, 0], 0)

roc_auc = roc_auc_score(y_test, y_prob)
print(f"\nROC-AUC Score: {roc_auc:.4f}")

print("\nОтчёт классификации:")
print(classification_report(y_test, y_pred))

feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values(by='importance', ascending=False)

print(f"\nТоп 10 важных факторов:\n{feature_importance.head(10)}")

plt.figure(figsize=(10, 8))
sns.barplot(x='importance', y='feature', data=feature_importance.head(10), palette='viridis')
plt.title("Feature Importance for High Engagement Prediction")
plt.xlabel('Importance')
plt.ylabel('Feature')
plt.tight_layout()

plt.savefig(OUTPUT_PLOT_PATH)
print(f"График сохранен: {OUTPUT_PLOT_PATH}")
plt.show()

feature_importance.to_csv(OUTPUT_FEATURE_IMPORTANCE_PATH, index=False)
print(f"Таблица важности признаков сохранена: {OUTPUT_FEATURE_IMPORTANCE_PATH}")