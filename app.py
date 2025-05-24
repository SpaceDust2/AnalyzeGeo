from utils.data_processor import DataProcessor
from utils.analyzer import ResultAnalyzer
from utils.display import (
    display_search_result,
    display_search_results_grid,
    display_statistics_cards,
    create_filter_sidebar,
    apply_filters,
    create_export_section
)
import streamlit as st
import pandas as pd
import json
import time
import logging
import os
import sys
import requests
sys.path.append("llm")


# Настройка логирования для Streamlit
logging.basicConfig(level=logging.INFO)

# Импорт модулей

# Импорт локального браузерного агента
try:
    from utils.browser_agent import run_local_browser_search
    BROWSER_AVAILABLE = True
except ImportError as e:
    BROWSER_AVAILABLE = False
    st.error(f"❌ Локальный браузерный агент недоступен: {str(e)}")

# Настройка страницы
st.set_page_config(
    page_title="🤖 Локальный ИИ Поиск Адресов",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .search-result {
        padding: 10px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .text-analysis {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .extracted-text {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🤖 Локальный ИИ Поиск Адресов</h1>
    <p>Автономный браузерный агент с ИИ анализом скриншотов</p>
</div>
""", unsafe_allow_html=True)

# Инициализация состояния
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if not BROWSER_AVAILABLE:
    st.error("""
    ❌ **Локальный браузерный агент недоступен!**
    
    Для работы приложения установите зависимости:
    
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
    
    Также может потребоваться установка Tesseract OCR:
    - Windows: https://github.com/UB-Mannheim/tesseract/wiki
    - Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-rus`
    - macOS: `brew install tesseract tesseract-lang`
    """)
    st.stop()

# Вкладки
tab1, tab2, tab3, tab4, tab_verdict, tab5 = st.tabs(
    ["🚀 Поиск", "📊 Результаты", "🤖 ИИ Анализ", "📈 Аналитика", "🧑‍⚖️ Вердикт", "⚙️ Настройки"])

with tab1:
    st.header("🚀 Локальный поиск адресов")

    st.info("""
    **🤖 Особенности локального ИИ агента:**
    - ✅ Полностью автономная работа без внешних API
    - 🌐 Реальный браузер Chrome для обхода блокировок
    - 📸 Автоматические скриншоты каждого поиска
    - 🤖 ИИ анализ скриншотов и извлечение текста
    - 💾 Сохранение текста в отдельные файлы
    - 🛡️ Определение капчи и проблем
    """)

    # Выбор способа загрузки
    input_method = st.radio(
        "Выберите способ загрузки данных:",
        ["📁 Загрузить файл", "📝 Вставить JSON"],
        horizontal=True
    )

    addresses = []
    data = []

    if input_method == "📁 Загрузить файл":
        uploaded_file = st.file_uploader(
            "Выберите JSON файл с адресами",
            type=['json'],
            help="Файл должен содержать массив объектов с полем 'address'"
        )

        if uploaded_file is not None:
            try:
                data = DataProcessor.load_json_file(uploaded_file)
                addresses = DataProcessor.extract_addresses(data)
                st.success(f"✅ Загружено {len(addresses)} адресов")

                # Показываем превью
                with st.expander("👀 Просмотр загруженных адресов"):
                    for i, addr in enumerate(addresses[:10]):
                        st.text(f"{i+1}. {addr}")
                    if len(addresses) > 10:
                        st.text(f"... и еще {len(addresses) - 10} адресов")

            except Exception as e:
                st.error(f"❌ Ошибка загрузки файла: {str(e)}")

    else:  # Вставить JSON
        json_text = st.text_area(
            "Вставьте JSON данные:",
            height=300,
            placeholder='[\n  {\n    "address": "Москва, ул. Тверская, д. 1"\n  }\n]'
        )

        if json_text:
            try:
                data = DataProcessor.parse_json_text(json_text)
                addresses = DataProcessor.extract_addresses(data)
                st.success(f"✅ Распознано {len(addresses)} адресов")
            except Exception as e:
                st.error(f"❌ Ошибка парсинга JSON: {str(e)}")

    # Настройки браузера
    st.subheader("🔧 Настройки браузерного агента")
    col1, col2, col3 = st.columns(3)

    with col1:
        headless_mode = st.checkbox(
            "🔇 Скрытый режим",
            value=True,
            help="Запуск браузера без отображения окна"
        )

    with col2:
        save_screenshots = st.checkbox(
            "📸 Сохранять скриншоты",
            value=True,
            help="Автоматически сохранять скриншоты поисковой выдачи"
        )

    with col3:
        max_addresses = st.number_input(
            "📊 Максимум адресов",
            min_value=1,
            max_value=50,
            value=min(10, len(addresses)) if addresses else 5,
            help="Ограничение для предотвращения долгого ожидания"
        )

    # Предупреждение о времени
    if addresses:
        # ~15 сек на адрес
        estimated_time = len(addresses[:max_addresses]) * 15
        st.info(
            f"⏱️ Примерное время выполнения: {estimated_time // 60} мин {estimated_time % 60} сек")

    # Кнопка запуска
    if st.button("🚀 Запустить локальный поиск", type="primary", disabled=len(addresses) == 0):
        if len(addresses) > max_addresses:
            addresses = addresses[:max_addresses]
            st.warning(f"⚠️ Ограничено до {max_addresses} адресов")

        st.session_state.search_results = []

        # Прогресс бар
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Контейнер для результатов в реальном времени
        results_container = st.container()

        def progress_callback(current, total, address):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(
                f"🔍 Поиск {current + 1}/{total}: {address[:50]}...")

        with st.spinner("🤖 Запускаем локальный браузерный агент..."):
            try:
                # Запускаем локальный браузерный поиск
                browser_results = run_local_browser_search(
                    addresses,
                    headless=headless_mode,
                    progress_callback=progress_callback
                )

                # Преобразуем результаты для совместимости
                all_results = []
                for browser_result in browser_results:
                    if browser_result.get('results'):
                        for result in browser_result['results']:
                            result['address'] = browser_result['address']
                            all_results.append(result)

                # Сохраняем результаты
                st.session_state.search_results = all_results
                st.session_state.browser_results = browser_results
                st.session_state.results_df = DataProcessor.results_to_dataframe(
                    all_results)

                progress_bar.progress(1.0)
                status_text.text("✅ Локальный поиск завершен!")

                # Показываем итоговую статистику
                successful_searches = sum(
                    1 for r in browser_results if r.get('success', False))
                screenshots_count = sum(
                    1 for r in browser_results if r.get('screenshot_path'))
                text_files_count = sum(
                    1 for r in browser_results if r.get('text_file_path'))
                st.success(f"""
                🎉 **Поиск завершен!**
                - Обработано адресов: {len(browser_results)}
                - Успешных поисков: {successful_searches}
                - Найдено результатов: {len(all_results)}
                - Скриншотов создано: {screenshots_count}
                - Файлов текста: {text_files_count}
                """)

                # Показываем краткие результаты по каждому адресу
                with results_container:
                    st.subheader("🔍 Краткие результаты:")
                    for result in browser_results:
                        if result.get('success'):
                            st.success(
                                f"✅ {result['address']}: {len(result.get('results', []))} результатов")
                        else:
                            st.error(
                                f"❌ {result['address']}: {result.get('error', 'Неизвестная ошибка')}")

            except Exception as e:
                st.error(f"❌ Ошибка локального поиска: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

with tab2:
    st.header("📊 Результаты поиска")

    if not st.session_state.results_df.empty:
        # Фильтры в сайдбаре
        filters = create_filter_sidebar(st.session_state.results_df)

        # Применяем фильтры
        filtered_df = apply_filters(st.session_state.results_df, filters)

        # Статистика по отфильтрованным данным
        if not filtered_df.empty:
            analyzer = ResultAnalyzer(filtered_df)
            stats = analyzer.calculate_relevance_stats()
            display_statistics_cards(stats)

            st.markdown("---")

            # Переключатель вида
            view_mode = st.radio(
                "Режим отображения:",
                ["🔍 Поисковая выдача", "📊 Таблица"],
                horizontal=True
            )

            if view_mode == "🔍 Поисковая выдача":
                # Группировка по адресам
                address_filter = st.selectbox(
                    "Выберите адрес:",
                    ["Все адреса"] +
                    sorted(filtered_df['address'].unique().tolist())
                )

                if address_filter != "Все адреса":
                    display_df = filtered_df[filtered_df['address']
                                             == address_filter]
                else:
                    display_df = filtered_df

                # Отображение результатов
                st.subheader(f"Результаты поиска ({len(display_df)} записей)")

                # Сортировка
                display_df = display_df.sort_values(['address', 'rank'])

                # Группируем по адресам для красивого отображения
                for address in display_df['address'].unique():
                    st.markdown(f"### 📍 {address}")
                    address_results = display_df[display_df['address'] == address].to_dict(
                        'records')
                    display_search_results_grid(address_results, columns=1)

            else:  # Табличный вид
                st.subheader(
                    f"Таблица результатов ({len(filtered_df)} записей)")

                # Интерактивная таблица
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=600,
                    column_config={
                        "url": st.column_config.LinkColumn("URL"),
                        "rank": st.column_config.NumberColumn("Позиция", format="%d"),
                    }
                )

            # Экспорт
            st.markdown("---")
            create_export_section(filtered_df)

        else:
            st.warning("Нет результатов, соответствующих выбранным фильтрам")

    else:
        st.info("👆 Сначала запустите поиск на вкладке 'Поиск'")

with tab3:
    st.header("🤖 ИИ Анализ скриншотов")

    if 'browser_results' in st.session_state and st.session_state.browser_results:

        # Статистика
        total_results = len(st.session_state.browser_results)
        successful_results = sum(
            1 for r in st.session_state.browser_results if r.get('success'))
        screenshots_count = sum(
            1 for r in st.session_state.browser_results if r.get('screenshot_path'))
        text_files_count = sum(
            1 for r in st.session_state.browser_results if r.get('text_file_path'))

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего поисков", total_results)
        with col2:
            st.metric("Успешных", successful_results)
        with col3:
            st.metric("Скриншотов", screenshots_count)
        with col4:
            st.metric("Файлов текста", text_files_count)

        st.markdown("---")

        # Отображение результатов анализа
        for idx, result in enumerate(st.session_state.browser_results):
            with st.expander(f"🤖 {result['address']}", expanded=False):

                col1, col2 = st.columns([3, 2])

                with col1:
                    # ИИ анализ текста
                    if result.get('ai_text_analysis'):
                        st.markdown("**🤖 ИИ Анализ скриншота:**")
                        st.markdown('<div class="text-analysis">',
                                    unsafe_allow_html=True)
                        st.text(result['ai_text_analysis'])
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Показываем файл с извлеченным текстом
                    if result.get('text_file_path') and os.path.exists(result['text_file_path']):
                        st.markdown("**📄 Извлеченный текст из файла:**")
                        try:
                            with open(result['text_file_path'], 'r', encoding='utf-8') as f:
                                extracted_text = f.read()

                            st.markdown('<div class="extracted-text">',
                                        unsafe_allow_html=True)
                            st.text(extracted_text)
                            st.markdown('</div>', unsafe_allow_html=True)

                            # Кнопка скачивания текста
                            st.download_button(
                                label="💾 Скачать текст",
                                data=extracted_text,
                                file_name=f"extracted_text_{idx+1}.txt",
                                mime="text/plain"
                            )

                        except Exception as e:
                            st.error(f"❌ Ошибка чтения файла: {str(e)}")

                    # Обычный анализ текста страницы
                    if result.get('text_analysis'):
                        st.markdown("**📝 Анализ DOM текста:**")
                        st.info(result['text_analysis'])

                with col2:
                    # Показываем скриншот
                    if result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
                        st.markdown("**📸 Скриншот поиска:**")
                        try:
                            st.image(
                                result['screenshot_path'],
                                caption=f"Скриншот: {result['address'][:30]}...",
                                use_column_width=True
                            )

                            # Кнопка скачивания скриншота
                            with open(result['screenshot_path'], "rb") as file:
                                st.download_button(
                                    label="📸 Скачать скриншот",
                                    data=file.read(),
                                    file_name=f"screenshot_{idx+1}.png",
                                    mime="image/png"
                                )

                        except Exception as e:
                            st.error(
                                f"❌ Ошибка отображения скриншота: {str(e)}")
                    else:
                        st.info("📷 Скриншот не найден")

                    # Статус и метаданные
                    if result.get('success'):
                        st.success("✅ Поиск успешен")
                    else:
                        st.error("❌ Ошибка поиска")
                        if result.get('error'):
                            st.error(f"Ошибка: {result['error']}")

                    # Найденные результаты
                    results_count = len(result.get('results', []))
                    st.metric("Результатов найдено", results_count)

                    if results_count > 0:
                        st.markdown("**🔗 Первые результаты:**")
                        for i, res in enumerate(result.get('results', [])[:3]):
                            st.text(
                                f"{i+1}. {res.get('title', 'Без названия')[:40]}...")

        # Кнопка очистки
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("🗑️ Очистить все результаты", type="secondary"):
                if 'browser_results' in st.session_state:
                    del st.session_state.browser_results
                if 'search_results' in st.session_state:
                    st.session_state.search_results = []
                if 'results_df' in st.session_state:
                    st.session_state.results_df = pd.DataFrame()
                st.success("✅ Все результаты очищены")
                st.rerun()

    else:
        st.info("👆 Сначала запустите поиск на вкладке 'Поиск'")

with tab4:
    st.header("📈 Аналитика")

    if not st.session_state.results_df.empty:
        analyzer = ResultAnalyzer(st.session_state.results_df)

        # Основная статистика
        stats = analyzer.calculate_relevance_stats()
        display_statistics_cards(stats)

        st.markdown("---")

        # Графики
        col1, col2 = st.columns(2)

        with col1:
            # Круговая диаграмма доменов
            fig_domains = analyzer.create_domain_pie_chart()
            st.plotly_chart(fig_domains, use_container_width=True)

        with col2:
            # Гистограмма типов результатов
            fig_types = analyzer.create_type_bar_chart()
            st.plotly_chart(fig_types, use_container_width=True)

        # График топ доменов
        st.subheader("📊 Топ доменов")
        top_n = st.slider("Количество доменов", 5, 20, 10)
        fig_top_domains = analyzer.create_top_domains_chart(top_n)
        st.plotly_chart(fig_top_domains, use_container_width=True)

        # Анализ позиций
        st.subheader("📈 Анализ позиций по типам результатов")
        position_df = analyzer.get_position_analysis()
        st.dataframe(
            position_df,
            use_container_width=True,
            column_config={
                "avg_position": st.column_config.NumberColumn("Средняя позиция", format="%.2f"),
                "min_position": st.column_config.NumberColumn("Мин. позиция", format="%d"),
                "max_position": st.column_config.NumberColumn("Макс. позиция", format="%d"),
                "count": st.column_config.NumberColumn("Количество", format="%d")
            }
        )

        # Успешность поиска
        if 'browser_results' in st.session_state:
            st.subheader("🎯 Статистика поиска")

            total_searches = len(st.session_state.browser_results)
            successful = sum(
                1 for r in st.session_state.browser_results if r.get('success', False))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего поисков", total_searches)
            with col2:
                st.metric("Успешных", successful)
            with col3:
                success_rate = (successful / total_searches *
                                100) if total_searches > 0 else 0
                st.metric("Успешность", f"{success_rate:.1f}%")

    else:
        st.info("👆 Сначала запустите поиск на вкладке 'Поиск'")

with tab_verdict:
    st.header("🧑‍⚖️ Вердикт: Коммерческая деятельность по адресу")
    st.info("Для каждого адреса анализируется текст выдачи и даётся краткий вывод LLM: ведётся ли коммерческая деятельность по адресу и почему.")

    if 'browser_results' in st.session_state and st.session_state.browser_results:
        for idx, result in enumerate(st.session_state.browser_results):
            with st.expander(f"{result['address']}", expanded=False):
                # Извлечённый текст
                extracted_text = ""
                if result.get('text_file_path') and os.path.exists(result['text_file_path']):
                    try:
                        with open(result['text_file_path'], 'r', encoding='utf-8') as f:
                            extracted_text = f.read()
                    except Exception as e:
                        extracted_text = result.get('ai_text_analysis', '')
                else:
                    extracted_text = result.get('ai_text_analysis', '')

                st.markdown("**📄 Извлечённый текст для анализа:**")
                st.text_area("Текст для LLM", value=extracted_text,
                             height=200, key=f"text_{idx}")

                if st.button(f"Получить вердикт по адресу {idx+1}", key=f"verdict_btn_{idx}"):
                    with st.spinner("LLM анализирует текст через API..."):
                        prompt = f"Вот фрагмент поисковой выдачи и анализа по адресу. Определи, ведётся ли по этому адресу коммерческая деятельность (магазин, офис, услуги, аренда, производство и т.п.)? Ответь только 'Да' или 'Нет' и кратко объясни почему, ссылаясь на факты из текста.\n\nТекст:\n{extracted_text}\n\nВердикт:"
                        system_prompt = "Ты — эксперт по анализу коммерческой деятельности по адресу. Отвечай кратко, тезисно, только по фактам из текста."
                        try:
                            response = requests.post(
                                "http://10.2.0.244:8000/chat",
                                json={
                                    "prompt": prompt,
                                    "system_prompt": system_prompt,
                                    "max_tokens": 128,
                                    "temperature": 0.1
                                },
                                timeout=60
                            )
                            if response.status_code == 200:
                                data = response.json()
                                verdict = data.get(
                                    "response", "[Нет ответа от LLM]")
                                st.success(f"**Вердикт:** {verdict}")
                            else:
                                st.error(
                                    f"Ошибка API: {response.status_code} {response.text}")
                        except Exception as e:
                            st.error(f"Ошибка запроса к LLM API: {str(e)}")
    else:
        st.info("Сначала запусти поиск и анализ на предыдущих вкладках.")

with tab5:
    st.header("⚙️ Настройки и информация")

    st.subheader("🤖 Локальный браузерный агент")

    if BROWSER_AVAILABLE:
        st.success("✅ Локальный браузерный агент доступен")

        st.markdown("""
        **🔧 Возможности агента:**
        - 🌐 Реальный браузер Chrome/Chromium
        - 📸 Автоматические скриншоты в высоком качестве  
        - 🤖 Локальная ИИ модель для анализа изображений
        - 📝 OCR для извлечения текста из скриншотов
        - 💾 Сохранение текста в отдельные файлы
        - 🛡️ Автоматическое определение капчи
        - 🎨 Анализ цветов и структуры страницы
        - ⚡ Полностью автономная работа
        """)

    else:
        st.error("❌ Локальный браузерный агент недоступен")

    st.subheader("📁 Файловая структура")

    # Показываем информацию о созданных папках и файлах
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📸 Скриншоты:**")
        screenshots_dir = "screenshots"
        if os.path.exists(screenshots_dir):
            files = os.listdir(screenshots_dir)
            st.info(f"📁 {screenshots_dir}/ ({len(files)} файлов)")
            if files:
                total_size = sum(os.path.getsize(os.path.join(screenshots_dir, f))
                                 for f in files if os.path.isfile(os.path.join(screenshots_dir, f)))
                st.text(f"Общий размер: {total_size / 1024 / 1024:.1f} МБ")
        else:
            st.info("📁 screenshots/ (папка будет создана)")

    with col2:
        st.markdown("**📄 Извлеченный текст:**")
        text_dir = "extracted_text"
        if os.path.exists(text_dir):
            files = os.listdir(text_dir)
            st.info(f"📁 {text_dir}/ ({len(files)} файлов)")
            if files:
                total_size = sum(os.path.getsize(os.path.join(text_dir, f))
                                 for f in files if os.path.isfile(os.path.join(text_dir, f)))
                st.text(f"Общий размер: {total_size / 1024:.1f} КБ")
        else:
            st.info("📁 extracted_text/ (папка будет создана)")

    st.subheader("📋 Установка и настройка")

    with st.expander("💻 Команды для установки"):
        st.code("""
# Основные зависимости
pip install -r requirements.txt

# Браузер Chromium
playwright install chromium

# Tesseract OCR (для извлечения текста)
# Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-rus  
# macOS: brew install tesseract tesseract-lang
        """)

    with st.expander("🔧 Системные требования"):
        st.markdown("""
        **Минимальные требования:**
        - RAM: 4 GB (рекомендуется 8 GB)
        - Свободное место: 1 GB для браузера + место для скриншотов
        - Python 3.8+
        - Операционная система: Windows 10+, macOS 10.14+, Ubuntu 18.04+
        
        **Примерная производительность:**
        - ~10-15 секунд на адрес
        - ~2-5 МБ на скриншот
        - ~1-5 КБ на файл текста
        - Может работать с капчами и блокировками
        """)

    st.subheader("📊 Логи текущей сессии")

    if 'search_results' in st.session_state and st.session_state.search_results:
        st.write(
            f"🔍 Найдено результатов: {len(st.session_state.search_results)}")
        st.write(
            f"📍 Уникальных адресов: {st.session_state.results_df['address'].nunique() if not st.session_state.results_df.empty else 0}")

    if 'browser_results' in st.session_state and st.session_state.browser_results:
        st.write(
            f"🤖 Браузерных поисков: {len(st.session_state.browser_results)}")

        # Показываем статистику скриншотов
        screenshots_count = sum(
            1 for r in st.session_state.browser_results if r.get('screenshot_path'))
        text_files_count = sum(
            1 for r in st.session_state.browser_results if r.get('text_file_path'))
        st.write(f"📸 Скриншотов создано: {screenshots_count}")
        st.write(f"📄 Файлов текста: {text_files_count}")

        # Показываем ошибки
        errors = [r.get('error')
                  for r in st.session_state.browser_results if r.get('error')]
        if errors:
            st.write(f"⚠️ Ошибок: {len(errors)}")
            with st.expander("Показать ошибки"):
                for error in errors:
                    st.text(f"• {error}")

    if not st.session_state.get('search_results') and not st.session_state.get('browser_results'):
        st.info("Логи появятся после запуска поиска")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🤖 <strong>Локальный ИИ Поиск Адресов v2.0</strong></p>
    <p>Полностью автономный • С ИИ анализом • Извлечение текста в файлы</p>
    <p>Создано с ❤️ используя Streamlit + Playwright + OpenCV + Tesseract</p>
</div>
""", unsafe_allow_html=True)
