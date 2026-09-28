import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency

df = pd.read_csv('ecommerce_clean.csv')
print(df.head(), df.describe()); print("\n", df.shape[0], df.shape[1])

features = ['age', 'gender', 'device_type', 'time_on_site', 'pages_viewed',
            'previous_purchases', 'cart_items', 'discount_seen', 'ad_clicked',
            'returning_user', 'avg_session_time', 'bounce_rate']
target = 'purchase'

numeric_cols = df.select_dtypes(include='number').columns.tolist()
if 'user_id' in numeric_cols:
    numeric_cols.remove('user_id')

correlation_matrix = df[numeric_cols].corr()[target].sort_values(ascending=False)
print(correlation_matrix.head(10))

plt.figure(figsize=(10, 8))
sns.heatmap(df[numeric_cols].corr(), annot=True, fmt='.2f', cmap='coolwarm', square=True, linewidths=.5)
plt.title('Матрица числовых признаков')
plt.savefig('eda_correlation_matrix.png')
plt.show()

plt.figure(figsize = (10, 6))
sns.boxplot(x=target, y='time_on_site', data=df)
plt.title('Время на сайте: Покупатели vs Не покупатели')
plt.xlabel('Покупка (0 - Нет, 1 - Да)')
plt.ylabel('Время на сайте (минуты)')
plt.savefig('eda_time_distribution.png')
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.countplot(x='device_type', hue=target, data=df, ax=axes[0], palette='viridis')
axes[0].set_title('Конверсия по типам устройств')
axes[0].legend(title='Покупка')

sns.countplot(x='gender', hue=target, data=df, ax=axes[1], palette='viridis')
axes[1].set_title('Конверсия по полу')
axes[1].legend(title='Покупка')
plt.tight_layout()
plt.savefig('eda_categorical_analysis.png')
plt.show()

group_with_discount = df[df['discount_seen'] == 1]['cart_items'].dropna()
group_without_discount = df[df['discount_seen'] == 0]['cart_items'].dropna()

print(f"Группа со скидкой: {len(group_with_discount)} наблюдений")
print(f"Группа без скидки: {len(group_without_discount)} наблюдений")

if len(group_with_discount) <= 5000 and len(group_without_discount) <= 5000:
    try:
        stat_w, p_value_w = stats.shapiro(group_with_discount.values[:min(len(group_with_discount), 5000)])
        print(f"Тест Шапиро-Уилка (подвыборка): statistic={stat_w:.4f}, p-value={p_value_w:.4f}")

        if p_value_w > 0.05:
            is_normal = True
            print("Данные близки к нормальному распределению.")
        else:
            is_normal = False
            print("Данные НЕ соответствуют нормальному распределению.")

    except Exception as e:
        print(f"Ошибка при тестировании нормальности: {e}. Считаем данные ненормальными.")
        is_normal = False
else:
    print("Выборка слишком велика для надежного теста Шапиро-Уилка. Предполагаем ненормальность.")
    is_normal = False

alpha = 0.05
if is_normal:
    print(" Используем Welch's t-test (для нормальных данных)")
    test_stat, p_val = stats.ttest_ind(group_with_discount, group_without_discount, equal_var=False)
    test_name = "Welch's t-test"
else:
    print(" Используем Mann-Whitney U test (для ненормальных данных / ординальных шкал)")
    test_stat, p_val = stats.mannwhitneyu(group_with_discount, group_without_discount, alternative='two-sided')
    test_name = "Mann-Whitney U Test"

mean_with = group_with_discount.mean()
mean_without = group_without_discount.mean()

if p_val < alpha:
    conclusion_1 = f"ГИПОТЕЗА ПОДТВЕРЖДЕНА: Разница в среднем размере корзины статистически значима (p-value = {p_val:.4f})."
else:
    conclusion_1 = f"ГИПОТЕЗА ОТВЕРГНУТА: Разница в среднем размере корзины НЕ является статистически значимой (p-value = {p_val:.4f})."

print("\n" + "=" * 50)
print(f"Результат теста: {test_name}")
print(conclusion_1)
print(f"Средняя корзина (со скидкой): {mean_with:.2f} товаров")
print(f"Средняя корзина (без скидки): {mean_without:.2f} товаров")
print("=" * 50)

overall_conversion = df[target].mean()
conversion_by_device = df.groupby('device_type')[target].agg(['count', 'sum', 'mean']).rename(
    columns = {
        'count': 'total_users',
        'mean':'conversion_rate',
        'sum':'buyers'
    })
conversion_by_discount = df.groupby('discount_seen')[target].agg(['count', 'sum', 'mean']).rename(
    columns = {
        'count':'total_users',
        'mean':'conversion_rate',
        'sum':'buyers'
    })
print(conversion_by_device.sort_values('conversion_rate', ascending=False))
print(f"conversion_by_discount: \n{conversion_by_discount}")

contingency_table = pd.crosstab(df['device_type'], df['purchase'])
chi2, p_chi, dof, expected_freq = chi2_contingency(contingency_table)
print("\nТест Xи-квадрат для влияния на покупку:")
print(f"p-value: {p_chi:.4f}")
if p_chi < 0.05:
    print("=>Скидка статистически значимо влияет на факт покупки")
else:
    print("Скидка не оказывает статистически значимого влияния на факт покупки ")

conversion_by_device.reset_index().to_csv('sql_results/conversion_by_device.csv', index=False)
conversion_by_discount.reset_index().to_csv("sql_results/conversion_by_discount.csv", index=False)

group_disc_buyers = df[df['discount_seen'] == 1][target]
group_nodisc_buyers = df[df['discount_seen'] == 0][target]

with open('hypothesis_results.txt', 'a', encoding='utf-8') as f:
    f.write(f"{test_name} for Discount impact on Cart Items:\n")
    f.write(f"P-value: {p_val:.6f}\n")
    f.write(f"Mean With Discount: {mean_with:.2f}\n")
    f.write(f"Without Discount: {mean_without:.2f}\n")
    f.write(f"Conclusion: {conclusion_1}\n\n")