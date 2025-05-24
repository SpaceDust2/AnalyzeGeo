import streamlit as st
from typing import Dict, List
import pandas as pd
import json


def display_search_result(result: Dict):
    """Отображение одного результата поиска в стиле Яндекса"""
    with st.container():
        # Заголовок со ссылкой
        title_html = f'<h3 style="margin: 0; font-size: 18px;"><a href="{result["url"]}" target="_blank" style="color: #1a0dab; text-decoration: none;">{result["title"]}</a></h3>'
        st.markdown(title_html, unsafe_allow_html=True)

        # URL и тип результата
        domain_type = f'<p style="margin: 0; color: #006621; font-size: 14px;">{result["domain"]} • {get_result_type_emoji(result["result_type"])} {get_result_type_name(result["result_type"])}</p>'
        st.markdown(domain_type, unsafe_allow_html=True)

        # Сниппет
        if result['snippet']:
            st.markdown(
                f'<p style="margin: 5px 0; color: #545454; font-size: 14px; line-height: 1.4;">{result["snippet"]}</p>', unsafe_allow_html=True)

        # Дополнительная информация
        if result['additional_info']:
            st.markdown(
                f'<p style="margin: 0; color: #70757a; font-size: 12px; font-style: italic;">{result["additional_info"]}</p>', unsafe_allow_html=True)

        st.markdown(
            '<hr style="margin: 15px 0; border: none; border-top: 1px solid #ebebeb;">', unsafe_allow_html=True)


def get_result_type_emoji(result_type: str) -> str:
    """Получить эмодзи для типа результата"""
    emojis = {
        'maps': '🗺️',
        'maps_2gis': '📍',
        'realestate': '🏠',
        'government': '🏛️',
        'encyclopedia': '📚',
        'website': '🌐'
    }
    return emojis.get(result_type, '🔗')


def get_result_type_name(result_type: str) -> str:
    """Получить русское название типа результата"""
    names = {
        'maps': 'Карты',
        'maps_2gis': '2GIS',
        'realestate': 'Недвижимость',
        'government': 'Госсайт',
        'encyclopedia': 'Энциклопедия',
        'website': 'Веб-сайт'
    }
    return names.get(result_type, 'Сайт')


def display_search_results_grid(results: List[Dict], columns: int = 1):
    """Отображение результатов в виде сетки"""
    if columns == 1:
        for result in results:
            display_search_result(result)
    else:
        # Разбиваем результаты на колонки
        cols = st.columns(columns)
        for idx, result in enumerate(results):
            with cols[idx % columns]:
                display_search_result(result)


def display_statistics_cards(stats: Dict):
    """Отображение карточек со статистикой"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Всего результатов", stats['total_results'])

    with col2:
        st.metric("Уникальных адресов", stats['unique_addresses'])

    with col3:
        st.metric("Результатов на адрес",
                  f"{stats['avg_results_per_address']:.1f}")

    with col4:
        st.metric("Покрытие картами", f"{stats['maps_coverage_percent']:.1f}%")


def create_filter_sidebar(df: pd.DataFrame) -> Dict:
    """Создание боковой панели с фильтрами"""
    st.sidebar.header("🔍 Фильтры")

    filters = {}

    # Фильтр по домену
    domains = ['Все'] + sorted(df['domain'].unique().tolist())
    selected_domain = st.sidebar.selectbox("Домен", domains)
    if selected_domain != 'Все':
        filters['domain'] = selected_domain

    # Фильтр по типу результата
    result_types = ['Все'] + sorted(df['result_type'].unique().tolist())
    selected_type = st.sidebar.selectbox("Тип результата", result_types)
    if selected_type != 'Все':
        filters['result_type'] = selected_type

    # Фильтр по позиции
    rank_range = st.sidebar.slider(
        "Позиция в выдаче",
        min_value=int(df['rank'].min()),
        max_value=int(df['rank'].max()),
        value=(int(df['rank'].min()), int(df['rank'].max()))
    )
    filters['rank_min'] = rank_range[0]
    filters['rank_max'] = rank_range[1]

    # Поиск по тексту
    search_text = st.sidebar.text_input("Поиск в результатах")
    if search_text:
        filters['search_text'] = search_text.lower()

    return filters


def apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """Применение фильтров к DataFrame"""
    filtered_df = df.copy()

    if 'domain' in filters:
        filtered_df = filtered_df[filtered_df['domain'] == filters['domain']]

    if 'result_type' in filters:
        filtered_df = filtered_df[filtered_df['result_type']
                                  == filters['result_type']]

    if 'rank_min' in filters and 'rank_max' in filters:
        filtered_df = filtered_df[
            (filtered_df['rank'] >= filters['rank_min']) &
            (filtered_df['rank'] <= filters['rank_max'])
        ]

    if 'search_text' in filters:
        mask = (
            filtered_df['title'].str.lower().str.contains(filters['search_text'], na=False) |
            filtered_df['snippet'].str.lower().str.contains(filters['search_text'], na=False) |
            filtered_df['address'].str.lower().str.contains(
                filters['search_text'], na=False)
        )
        filtered_df = filtered_df[mask]

    return filtered_df


def create_export_section(df: pd.DataFrame):
    """Создание секции экспорта данных"""
    st.subheader("📥 Экспорт результатов")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="Скачать CSV",
            data=csv.encode('utf-8-sig'),
            file_name="search_results.csv",
            mime="text/csv"
        )

    with col2:
        # Excel экспорт через временный файл
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Результаты', index=False)

        st.download_button(
            label="Скачать Excel",
            data=buffer.getvalue(),
            file_name="search_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col3:
        json_str = json.dumps(df.to_dict(orient='records'),
                              ensure_ascii=False, indent=2)
        st.download_button(
            label="Скачать JSON",
            data=json_str,
            file_name="search_results.json",
            mime="application/json"
        )
