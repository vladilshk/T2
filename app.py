import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Т2 - Оптимизация маршрутов", layout="wide")

st.title("🚀 Т2: Оптимизация маршрутов торговой команды")
st.markdown("*ИИ-система планирования и мониторинга*")

if 'employees' not in st.session_state:
    st.session_state.employees = ["Иванов", "Петров", "Сидоров", "Кузнецов"]
if 'tt_data' not in st.session_state:
    st.session_state.tt_data = None
if 'schedule' not in st.session_state:
    st.session_state.schedule = None

st.sidebar.header("⚙️ Настройки")
page = st.sidebar.radio("Раздел:", [
    "📊 Загрузка данных",
    "🗺️ Планирование маршрутов",
    "⚡ Форс-мажоры",
    "📈 Аналитика"
])

def generate_sample_data():
    districts = ["г.о. Саранск"] + [
        "Ардатовский", "Атюрьевский", "Атяшевский", "Большеберезниковский",
        "Большеигнатовский", "Дубёнский", "Ельниковский", "Зубово-Полянский",
        "Инсарский", "Ичалковский", "Кадошкинский", "Ковылкинский",
        "Кочкуровский", "Краснослободский", "Лямбирский", "Ромодановский",
        "Рузаевский", "Старошайговский", "Темниковский", "Теньгушевский",
        "Торбеевский", "Чамзинский"
    ]

    tt_list = []
    tt_id = 1
    categories = {
        'A': {'count': 50, 'visits_per_month': 3, 'time_per_visit': 45},
        'B': {'count': 75, 'visits_per_month': 2, 'time_per_visit': 30},
        'C': {'count': 50, 'visits_per_month': 1, 'time_per_visit': 20},
        'D': {'count': 75, 'visits_per_quarter': 1, 'time_per_visit': 15}
    }

    saransk_categories = ['A']*6 + ['B']*9 + ['C']*6 + ['D']*9
    for i, cat in enumerate(saransk_categories):
        info = categories[cat]
        visits = info.get('visits_per_month', info.get('visits_per_quarter', 1))
        if cat == 'D':
            visits = 0.33
        tt_list.append({
            'id': tt_id, 'name': f"ТТ-{tt_id:03d}", 'district': "г.о. Саранск",
            'category': cat, 'visits_per_month': visits,
            'time_per_visit': info['time_per_visit'],
            'lat': 54.18 + random.uniform(-0.05, 0.05),
            'lon': 45.18 + random.uniform(-0.05, 0.05)
        })
        tt_id += 1

    for district in districts[1:]:
        dist_categories = ['A']*2 + ['B']*3 + ['C']*2 + ['D']*3
        for cat in dist_categories:
            info = categories[cat]
            visits = info.get('visits_per_month', info.get('visits_per_quarter', 1))
            if cat == 'D':
                visits = 0.33
            angle = random.uniform(0, 2*3.14159)
            distance = random.uniform(0.3, 1.2)
            tt_list.append({
                'id': tt_id, 'name': f"ТТ-{tt_id:03d}", 'district': district,
                'category': cat, 'visits_per_month': visits,
                'time_per_visit': info['time_per_visit'],
                'lat': 54.18 + distance * np.cos(angle) * 0.5,
                'lon': 45.18 + distance * np.sin(angle) * 0.8
            })
            tt_id += 1
    return pd.DataFrame(tt_list)

def optimize_routes(tt_df, employees, start_date):
    schedule = []
    districts = tt_df['district'].unique()
    work_days = [start_date + timedelta(days=i) for i in range(5)]

    for day_idx, date in enumerate(work_days):
        day_schedule = {
            'date': date.strftime('%Y-%m-%d'),
            'day_name': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'][day_idx],
            'routes': {}
        }
        for emp_idx, employee in enumerate(employees):
            district = districts[(day_idx + emp_idx) % len(districts)]
            district_tt = tt_df[tt_df['district'] == district].copy()
            priority_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            district_tt['priority'] = district_tt['category'].map(priority_map)
            district_tt = district_tt.sort_values('priority')
            selected_tt = district_tt.head(8)

            route = []
            total_time = 0
            for _, tt in selected_tt.iterrows():
                if tt['visits_per_month'] >= 0.9:
                    should_visit = False
                    if tt['category'] == 'A':
                        should_visit = True
                    elif tt['category'] == 'B':
                        should_visit = (day_idx % 2 == 0)
                    elif tt['category'] == 'C':
                        should_visit = (day_idx == 0)

                    if should_visit and total_time + tt['time_per_visit'] <= 480:
                        route.append({
                            'tt_id': tt['id'], 'tt_name': tt['name'],
                            'district': tt['district'], 'category': tt['category'],
                            'duration': tt['time_per_visit'], 'status': 'planned'
                        })
                        total_time += tt['time_per_visit'] + 15

            day_schedule['routes'][employee] = {
                'employee': employee, 'district': district, 'points': route,
                'total_time': total_time, 'points_count': len(route)
            }
        schedule.append(day_schedule)
    return schedule

    # Раздел 1: Загрузка данных
if page == "📊 Загрузка данных":
    st.header("📊 База торговых точек")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Загрузка Excel")
        uploaded_file = st.file_uploader("Загрузите файл с ТТ", type=['xlsx', 'xls'])
        if uploaded_file:
            try:
                st.session_state.tt_data = pd.read_excel(uploaded_file)
                st.success("✅ Данные загружены!")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    with col2:
        st.subheader("Или демо-данные")
        if st.button("🎲 Сгенерировать по ТЗ"):
            st.session_state.tt_data = generate_sample_data()
            st.success("✅ Сгенерировано 250 ТТ!")

    if st.session_state.tt_data is not None:
        df = st.session_state.tt_data
        st.subheader("Статистика")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Всего ТТ", len(df))
        c2.metric("Районов", df['district'].nunique())
        c3.metric("Категория A", len(df[df['category'] == 'A']))
        c4.metric("Категория D", len(df[df['category'] == 'D']))
        st.bar_chart(df['category'].value_counts().sort_index())

# Раздел 2: Планирование
elif page == "🗺️ Планирование маршрутов":
    st.header("🗺️ Планирование маршрутов")
    if st.session_state.tt_data is None:
        st.warning("⚠️ Сначала загрузите данные")
    else:
        start_date = st.date_input("Начало недели", datetime.now())
        if st.button("🚀 Оптимизировать маршруты"):
            with st.spinner("Оптимизация..."):
                st.session_state.schedule = optimize_routes(
                    st.session_state.tt_data,
                    st.session_state.employees,
                    start_date
                )
            st.success("✅ Маршруты построены!")

        if st.session_state.schedule:
            for day in st.session_state.schedule:
                with st.expander(f"{day['day_name']} ({day['date']})"):
                    for emp, route in day['routes'].items():
                        st.markdown(f"**{emp}** → {route['district']}")
                        st.write(f"Точек: {route['points_count']}, Время: {route['total_time']//60}ч {route['total_time']%60}м")
                        if route['points']:
                            st.dataframe(pd.DataFrame(route['points'])[['tt_name', 'category', 'duration']])

# Раздел 3: Форс-мажоры
elif page == "⚡ Форс-мажоры":
    st.header("⚡ Обработка форс-мажоров")
    if st.session_state.schedule is None:
        st.warning("⚠️ Сначала постройте маршруты")
    else:
        affected = st.selectbox("Сотрудник недоступен:", st.session_state.employees)
        reason = st.selectbox("Причина:", ["Болезнь", "Поломка авто", "Погода"])
        day_name = st.selectbox("День:", [d['day_name'] for d in st.session_state.schedule])

        if st.button("⚠️ Активировать перераспределение"):
            day_data = next(d for d in st.session_state.schedule if d['day_name'] == day_name)
            points = day_data['routes'][affected]['points']
            st.error(f"❌ Отменён маршрут: {len(points)} точек")

            if points:
                others = [e for e in st.session_state.employees if e != affected]
                for i, p in enumerate(points):
                    target = others[i % len(others)]
                    st.success(f"✅ {target} получает: {p['tt_name']} (кат. {p['category']})")

# Раздел 4: Аналитика
elif page == "📈 Аналитика":
    st.header("📈 Аналитика")
    if st.session_state.schedule:
        total = sum(d['points_count'] for day in st.session_state.schedule for d in day['routes'].values())
        st.metric("Всего визитов", total)
        if st.button("📥 Сформировать отчёт"):
            st.info("Отчёт сформирован (в полной версии — скачивание Excel)")
