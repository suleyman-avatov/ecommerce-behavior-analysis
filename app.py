import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
import os

st.set_page_config(
    page_title='E-commerce Behavior Analysis', 
    layout="wide", 
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

DATA_PATH = os.path.join(DATA_DIR, 'ecommerce_clean.csv')
ML_FEATURES_PATH = os.path.join(DATA_DIR, 'ml_top_feature_engagement.csv')

@st.cache_data(ttl=600)
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(f" Файл данных не найден по пути: {DATA_PATH}")
        st.stop()
    return pd.read_csv(DATA_PATH)

@st.cache_data(ttl=600)
def load_ml_results():
    if os.path.exists(ML_FEATURES_PATH):
        try:
            df_imp = pd.read_csv(ML_FEATURES_PATH)
            return df_imp, True
        except Exception as e:
            st.warning(f"Не удалось прочитать ML файл: {e}. Используются демо-данные.")
            
    dummy_df = pd.DataFrame({
        'feature': ['time_on_site', 'pages_viewed', 'previous_purchases', 'returning_user', 'age'],
        'importance': [0.35, 0.25, 0.20, 0.15, 0.05]
    })
    return dummy_df, False

df = load_data()
features_imp_df, is_real_ml_data = load_ml_results()

if df.empty:
    st.error("Данные пусты.")
    st.stop()


df = load_data()
features_imp_df, is_real_ml_data = load_ml_results()

if df.empty:
    st.error("Данные пусты.")
    st.stop()

st.sidebar.header("⚙️ Управление")

with st.sidebar.expander("О проекте"):
    st.markdown("""
    **Автор:** Автов Сулейман Назимович  
    **Цель:** Анализ поведения пользователей e-commerce для выявления драйверов конверсии и сегментации аудитории.
    
    **Методология:**
    1. SQL ETL (Staging -> Marts)
    2. Статистические тесты (Mann-Whitney U)
    3. ML (Random Forest for Engagement Prediction)
    """)

st.sidebar.subheader(" Фильтры данных")
selected_device = st.sidebar.multiselect(
    "Тип устройств", 
    options=df['device_type'].unique(), 
    default=df['device_type'].unique()
)
selected_gender = st.sidebar.multiselect(
    "Пол", 
    options=df['gender'].unique(), 
    default=df['gender'].unique()
)
show_discount_only = st.sidebar.checkbox("Только со скидкой", value=False)

filtered_df = df.copy()
if selected_device:
    filtered_df = filtered_df[filtered_df['device_type'].isin(selected_device)]
if selected_gender:
    filtered_df = filtered_df[filtered_df['gender'].isin(selected_gender)]
if show_discount_only:
    filtered_df = filtered_df[filtered_df['discount_seen'] == 1]

if filtered_df.empty:
    st.warning("Нет данных для отображения при текущих фильтрах. Сбросьте их.")
    st.stop()

st.title("E-Commerce User Behavior Dashboard")
st.caption(f"Анализ {len(filtered_df):,} пользователей | Автор: Аватов Сулейман Назимович")

tab1, tab2, tab3 = st.tabs(["Обзор (KPI)", " Сегментация клиентов", "Инсайты и ML"])

with tab1:
    st.subheader("Ключевые показатели эффективности")

    col1, col2, col3, col4 = st.columns(4)

    total_users = len(filtered_df)
    conversion_rate = filtered_df['purchase'].mean() * 100 if total_users > 0 else 0
    avg_cart_size = filtered_df['cart_items'].mean() if total_users > 0 else 0
    avg_bounce_rate = filtered_df['bounce_rate'].mean() if total_users > 0 else 0

    with col1:
        st.metric(label="Всего пользователей", value=f"{total_users:,}")
    with col2:
        st.metric(label="Конверсия (%)", value=f"{conversion_rate:.2f}%")
    with col3:
        st.metric(label="Средняя корзина", value=f"{avg_cart_size:.2f}")
    with col4:
        st.metric(label="Ср. показатель отказов", value=f"{avg_bounce_rate:.2f}%")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Конверсия по устройствам")
        device_conv = filtered_df.groupby('device_type')['purchase'].mean().reset_index()
        device_conv['conversion_pct'] = device_conv['purchase'] * 100

        fig_bar = px.bar(
            device_conv,
            x='device_type',
            y='conversion_pct',
            text_auto=".2f",  
            labels={'conversion_pct': 'Конверсия (%)', 'device_type': 'Устройство'},  
            title='CR% по устройствам',                                              
            color='device_type',                                                     
            color_discrete_sequence=px.colors.qualitative.Set2                       
        )
        fig_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        csv_data = device_conv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=" Скачать данные конверсии (CSV)",
            data=csv_data,
            file_name='export_conversion_rates.csv',
            mime='text/csv'
        )

    with col_chart2:
        st.subheader("Распределение возрастных групп")
        bins = [17, 25, 35, 45, 55, 60]
        labels = ['18-25', '26-35', '36-45', '46-55', '56+']
        temp_df = filtered_df.copy()
        temp_df['age_group'] = pd.cut(temp_df['age'], bins=bins, labels=labels)
        
        age_dist = temp_df['age_group'].value_counts().reset_index()
        age_dist.columns = ['Age Group', 'Count']

        fig_pie = px.pie(age_dist, names="Age Group", values="Count", hole=0.4, title="Доли возрастных сегментов")
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Анализ вовлечённости и ценности клиента")

    def normalize(series):
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return series * 0
        return (series - min_val) / (max_val - min_val)

    filtered_df['eng_score'] = (
        normalize(filtered_df['time_on_site']) * 0.4 +
        normalize(filtered_df['pages_viewed']) * 0.3 +
        normalize(filtered_df['cart_items']) * 0.3
    )

    conditions = [
        (filtered_df['eng_score'] >= 0.7),
        (filtered_df['eng_score'] >= 0.4) & (filtered_df['eng_score'] < 0.7),
        (filtered_df['eng_score'] < 0.4)
    ]
    choices = ['High Value (Champions)', 'Medium Value', 'Low Value (Risk)']
    filtered_df['segment'] = np.select(conditions, choices, default="Unclassified")

    col_seg1, col_seg2 = st.columns([1, 2])

    with col_seg1:
        st.write("**Распределение по сегментам:**")
        seg_counts = filtered_df['segment'].value_counts()
        st.table(seg_counts.to_frame(name='Количество'))
        
        export_segments = filtered_df[['user_id', 'segment', 'eng_score']]
        st.download_button(
            label="⬇Скачать список сегментов (CSV)",
            data=export_segments.to_csv(index=False).encode('utf-8'),
            file_name='user_segments_export.csv',
            mime='text/csv'
        )

    with col_seg2:
        st.write("**Кластеризация: Время на сайте vs Товары в корзине**")
        sample_for_plot = filtered_df.sample(min(2000, len(filtered_df)))
        
        fig_scatter = px.scatter(sample_for_plot, x='time_on_site', y='cart_items', size='pages_viewed',
                                 color='segment', hover_name='user_id', 
                                 title='Визуализация кластеров пользователей', opacity=0.7,
                                 log_x=False, log_y=False)
        
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Топ-10 самых активных пользователей")
    top_users = filtered_df.nlargest(10, 'eng_score')[['user_id', 'age', 'gender', 'device_type', 'time_on_site', 'cart_items', 'segment']]
    st.dataframe(top_users.style.background_gradient(cmap='Blues'), use_container_width=True)

with tab3:
    st.subheader("Проверка бизнес-гипотез (A/B Testing)")
    st.info("Сравниваем группы 'Со скидкой' и 'Без скидки' по размеру корзины.")

    group_with_disc = filtered_df[filtered_df['discount_seen'] == 1]['cart_items']
    group_without_disc = filtered_df[filtered_df['discount_seen'] == 0]['cart_items']

    if len(group_with_disc) > 0 and len(group_without_disc) > 0:
        u_stat, p_value = stats.mannwhitneyu(group_with_disc, group_without_disc, alternative='two-sided')

        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.metric("P-value (значимость)", f"{p_value:.4f}")
            if p_value < 0.05:
                st.success(" Разница статистически значима (p < 0.05). Скидки влияют на корзину.")
            else:
                st.warning(" Разница НЕ значима (p >= 0.05). Скидки не меняют размер корзины существенно.")

        with col_res2:
            mean_with = group_with_disc.mean()
            mean_without = group_without_disc.mean()
            diff = mean_with - mean_without

            st.metric("Ср. корзина (со скидкой)", f"{mean_with:.2f}")
            st.metric("Ср. корзина (без скидки)", f"{mean_without:.2f}")
            st.metric("Разница", f"{diff:+.2f} товаров")

        st.subheader('Распределение размера корзины')
        fig_hist = px.histogram(filtered_df, x='cart_items', color='discount_seen', barmode='overlay',
                                histnorm='probability density', 
                                labels={'discount_seen': "Скидка?", 'cart_items': 'Товаров в корзине'},
                                title='Density Plot: Корзина со скидкой vs без')
        st.plotly_chart(fig_hist, use_container_width=True)

    else:
        st.warning("Недостаточно данных для сравнения групп после применения фильтров.")

    st.markdown("---")
    
    st.subheader("Feature Importance (Результаты ML-модели)")
    
    if not is_real_ml_data:
        st.warning(" Отображаются демо-данные. Для реальных результатов запустите обучение модели (`analysis/ml_modeling.py`).")
    
    top_features = features_imp_df.head(10).copy()
    
    fig_imp = px.bar(top_features.sort_values('importance', ascending=True),
                     x='importance', y='feature', orientation='h',
                     title="Какие факторы сильнее всего влияют на высокую вовлеченность?",
                     labels={'importance': 'Важность признака'})
    st.plotly_chart(fig_imp, use_container_width=True)
    
    st.download_button(
        label=" Скачать Feature Importance (CSV)",
        data=features_imp_df.to_csv(index=False).encode('utf-8'),
        file_name='feature_importance_latest.csv',
        mime='text/csv'
    )
