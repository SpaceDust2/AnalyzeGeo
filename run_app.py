#!/usr/bin/env python3
"""
🤖 Локальный ИИ Поиск Адресов v2.0
Скрипт быстрого запуска с проверками
"""

import sys
import os
import subprocess
import importlib


def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        return True


def check_dependencies():
    """Проверка основных зависимостей"""
    print("🔧 Проверка зависимостей...")

    required_packages = {
        'streamlit': 'Streamlit (веб-интерфейс)',
        'pandas': 'Pandas (обработка данных)',
        'plotly': 'Plotly (графики)',
        'playwright': 'Playwright (браузер)',
        'cv2': 'OpenCV (компьютерное зрение)',
        'numpy': 'NumPy (вычисления)',
        'PIL': 'Pillow (изображения)',
        'pytesseract': 'Tesseract OCR (извлечение текста)'
    }

    missing = []

    for package, description in required_packages.items():
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            else:
                importlib.import_module(package)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ❌ {description}")
            missing.append(package)

    if missing:
        print(f"\n❌ Отсутствуют зависимости: {', '.join(missing)}")
        print("💡 Установите командой: pip install -r requirements.txt")
        return False

    return True


def check_playwright():
    """Проверка браузера Playwright"""
    print("\n🌐 Проверка браузера...")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("  ✅ Браузер Chromium готов")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка браузера: {str(e)}")
                print("  💡 Установите командой: playwright install chromium")
                return False
    except ImportError:
        print("  ❌ Playwright не установлен")
        return False


def check_tesseract():
    """Проверка Tesseract OCR"""
    print("\n📝 Проверка Tesseract OCR...")

    try:
        import pytesseract
        # Пробуем извлечь текст из тестового изображения
        version = pytesseract.get_tesseract_version()
        print(f"  ✅ Tesseract {version} готов")
        return True
    except ImportError:
        print("  ❌ pytesseract не установлен")
        return False
    except Exception as e:
        print(f"  ⚠️ Tesseract установлен, но могут быть проблемы: {str(e)}")
        print("  💡 Проверьте установку Tesseract в системе")
        return True  # Не критично для работы


def create_directories():
    """Создание необходимых папок"""
    print("\n📁 Создание папок...")

    directories = ['screenshots', 'config', 'utils']

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✅ Создана папка: {directory}")
        else:
            print(f"  ✅ Папка существует: {directory}")


def run_streamlit():
    """Запуск Streamlit приложения"""
    print("\n🚀 Запуск приложения...")
    print("📱 Откроется в браузере: http://localhost:8501")
    print("⏹️ Для остановки нажмите Ctrl+C")
    print("-" * 50)

    try:
        subprocess.run([sys.executable, '-m', 'streamlit',
                       'run', 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка запуска: {e}")
        print("💡 Проверьте, что файл app.py существует")


def main():
    """Главная функция"""
    print("🤖 Локальный ИИ Поиск Адресов v2.0")
    print("=" * 50)

    # Проверки
    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies),
        ("Браузер", check_playwright),
        ("OCR", check_tesseract)
    ]

    all_good = True
    for name, check_func in checks:
        if not check_func():
            all_good = False

    # Создаем папки
    create_directories()

    if all_good:
        print("\n✅ Все проверки пройдены!")
        input("\nНажмите Enter для запуска приложения...")
        run_streamlit()
    else:
        print("\n⚠️ Есть проблемы с настройкой")
        print("\n📋 Инструкция по установке:")
        print("1. pip install -r requirements.txt")
        print("2. playwright install chromium")
        print("3. Установите Tesseract OCR для вашей ОС")
        print("\n💡 После установки запустите скрипт снова")


if __name__ == "__main__":
    main()
