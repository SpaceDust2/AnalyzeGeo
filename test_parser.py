#!/usr/bin/env python3
"""
Тест локального браузерного агента
"""

import logging
import sys
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Добавляем путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.browser_agent import run_local_browser_search

    def test_single_address():
        """Быстрый тест одного адреса с локальным браузерным агентом"""
        address = "Москва, улица Тверская, дом 1"

        print(f"🤖 Тестируем локальный браузерный агент")
        print(f"📍 Адрес: {address}")
        print("=" * 60)

        def progress_callback(current, total, addr):
            print(f"⏳ Прогресс: {current + 1}/{total} - {addr}")

        try:
            # Запускаем локальный поиск (не в headless режиме для наблюдения)
            results = run_local_browser_search(
                [address],
                headless=False,  # Показываем браузер для тестирования
                progress_callback=progress_callback
            )

            print("=" * 60)

            if results and len(results) > 0:
                result = results[0]

                print(f"✅ Результат получен!")
                print(
                    f"📊 Статус: {'Успех' if result.get('success') else 'Ошибка'}")

                if result.get('error'):
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print(
                        f"🔍 Найдено результатов в DOM: {len(result.get('results', []))}")

                    # Показываем первые несколько результатов
                    dom_results = result.get('results', [])
                    if dom_results:
                        print(f"\n📋 Первые результаты:")
                        for i, res in enumerate(dom_results[:3], 1):
                            print(
                                f"  {i}. {res.get('title', 'Без заголовка')}")
                            print(f"     🔗 {res.get('url', 'Без URL')}")
                            print(f"     🌐 {res.get('domain', 'Без домена')}")
                            print(
                                f"     🏷️ Тип: {res.get('result_type', 'неизвестно')}")
                            print()

                # Локальный анализ
                if result.get('local_analysis'):
                    print(f"🔍 Локальный анализ изображения:")
                    print(result['local_analysis'])
                    print()

                # Анализ текста
                if result.get('text_analysis'):
                    print(f"📝 Анализ текста страницы:")
                    print(result['text_analysis'])
                    print()

                # Информация о скриншоте
                if result.get('screenshot_path'):
                    print(f"📸 Скриншот сохранен: {result['screenshot_path']}")

                    # Проверяем размер файла
                    try:
                        import os
                        size = os.path.getsize(result['screenshot_path'])
                        print(f"📐 Размер файла: {size / 1024:.1f} KB")
                    except:
                        pass

            else:
                print("❌ Результаты не получены")
                print("\n💡 Возможные причины:")
                print("- Браузер не запустился")
                print("- Проблемы с сетью")
                print("- Капча или блокировка")
                print("- Не установлены зависимости")

        except Exception as e:
            print(f"❌ Критическая ошибка: {str(e)}")
            import traceback
            print(f"📋 Детали:\n{traceback.format_exc()}")

    def test_dependencies():
        """Проверка установленных зависимостей"""
        print("🔧 Проверка зависимостей:")
        print("-" * 40)

        # Проверяем основные библиотеки
        deps = {
            'playwright': 'Playwright (браузер)',
            'cv2': 'OpenCV (анализ изображений)',
            'numpy': 'NumPy (вычисления)',
            'PIL': 'Pillow (работа с изображениями)',
            'pytesseract': 'Tesseract OCR (извлечение текста)'
        }

        for module, description in deps.items():
            try:
                if module == 'cv2':
                    import cv2
                elif module == 'PIL':
                    from PIL import Image
                else:
                    __import__(module)
                print(f"✅ {description}")
            except ImportError:
                print(f"❌ {description} - НЕ УСТАНОВЛЕНО")

        print()

    if __name__ == "__main__":
        print("🤖 ТЕСТ ЛОКАЛЬНОГО БРАУЗЕРНОГО АГЕНТА")
        print("=" * 60)

        # Сначала проверяем зависимости
        test_dependencies()

        # Затем тестируем агента
        test_single_address()

        print("\n🚀 Для запуска полного приложения:")
        print("streamlit run app.py")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\n💡 Установите зависимости:")
    print("pip install -r requirements.txt")
    print("playwright install chromium")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
    import traceback
    traceback.print_exc()
