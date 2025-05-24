import json
import logging
import time
import re
import os
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
import numpy as np
import cv2
from PIL import Image
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Настройка логирования
logger = logging.getLogger(__name__)


class LocalBrowserAgent:
    """Локальный браузерный агент на Selenium/undetected-chromedriver"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.screenshots_dir = Path("screenshots")
        self.text_dir = Path("extracted_text")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)

    def open(self):
        logger.info("🚀 Запускаем локальный браузерный агент (Selenium)...")
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--lang=ru-RU')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.driver = uc.Chrome(options=options)
        logger.info("✅ Браузерный агент запущен")

    def close(self):
        if self.driver:
            self.driver.quit()
        logger.info("⛔ Браузерный агент остановлен")

    def search_address_in_yandex(self, address: str) -> Dict:
        logger.info(f"🔍 Ищем адрес в браузере: {address}")
        timestamp = int(time.time())
        safe_address = re.sub(r'[^\w\s-]', '', address).replace(' ', '_')[:30]
        safe_address = self._transliterate_russian(safe_address)
        screenshot_filename = f"search_{timestamp}_{safe_address}.png"
        text_filename = f"text_{timestamp}_{safe_address}.txt"
        screenshot_path = self.screenshots_dir / screenshot_filename
        text_path = self.text_dir / text_filename
        try:
            from urllib.parse import quote_plus
            search_url = f"https://yandex.ru/search/?text={quote_plus(address)}"
            logger.info(f"🌐 Переходим по прямому поисковому URL: {search_url}")
            # Скриншот ДО поиска (главная)
            try:
                self.driver.get("https://yandex.ru")
                time.sleep(2)
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"✅ Скриншот главной сохранен: {screenshot_path}")
            except Exception as e:
                logger.warning(
                    f"⚠️ Не удалось сделать скриншот главной: {str(e)}")
            # Переходим на страницу поиска
            self.driver.get(search_url)
            time.sleep(3)
            final_screenshot_path = self.screenshots_dir / \
                f"final_{screenshot_filename}"
            self.driver.save_screenshot(str(final_screenshot_path))
            logger.info(f"✅ Финальный скриншот: {final_screenshot_path}")
            # Извлекаем результаты из DOM
            results = self._extract_search_results_from_dom()
            # Анализируем скриншот с помощью ИИ
            ai_text_analysis = self._analyze_screenshot_with_ai(
                final_screenshot_path, address)
            # Сохраняем извлеченный текст в файл
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"Адрес: {address}\n")
                f.write(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Скриншот: {final_screenshot_path}\n")
                f.write("="*50 + "\n")
                f.write(ai_text_analysis)
            logger.info(f"💾 Текст сохранен в: {text_path}")
            # Получаем текст страницы для дополнительного анализа
            try:
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                text_analysis = self._analyze_page_text(page_text, address)
            except Exception as e:
                logger.error(f"❌ Ошибка получения текста страницы: {str(e)}")
                text_analysis = "Ошибка получения текста страницы"
            return {
                'address': address,
                'screenshot_path': str(final_screenshot_path),
                'text_file_path': str(text_path),
                'results': results,
                'ai_text_analysis': ai_text_analysis,
                'text_analysis': text_analysis,
                'page_title': self.driver.title,
                'page_url': self.driver.current_url,
                'success': True
            }
        except Exception as e:
            logger.error(f"❌ Ошибка поиска в браузере: {str(e)}")
            try:
                error_screenshot = self.screenshots_dir / \
                    f"error_{screenshot_filename}"
                self.driver.save_screenshot(str(error_screenshot))
                logger.info(f"📸 Скриншот ошибки сохранен: {error_screenshot}")
            except:
                pass
            return {
                'address': address,
                'error': str(e),
                'results': [],
                'ai_text_analysis': 'Ошибка при анализе',
                'text_analysis': 'Ошибка при анализе текста',
                'success': False
            }

    def _extract_search_results_from_dom(self) -> List[Dict]:
        results = []
        try:
            time.sleep(2)
            result_selectors = [
                '.serp-item', '.organic', 'li[data-cid]', '[data-log-node="serp-item"]',
                '.search-result', '.result', '.VanillaReact', '[data-bem*="serp-item"]'
            ]
            result_elements = []
            used_selector = None
            for selector in result_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    result_elements = elements
                    used_selector = selector
                    logger.info(
                        f"✅ Найдено {len(elements)} результатов с селектором: {selector}")
                    break
            if not result_elements:
                logger.warning(
                    "⚠️ Не найдено результатов поиска через селекторы")
                all_links = self.driver.find_elements(
                    By.CSS_SELECTOR, 'a[href]')
                logger.info(f"🔗 Найдено {len(all_links)} ссылок на странице")
                for i, link in enumerate(all_links[:10]):
                    try:
                        href = link.get_attribute('href')
                        text = link.text
                        if href and text and len(text.strip()) > 5:
                            results.append({
                                'rank': i + 1,
                                'title': text.strip()[:100],
                                'url': href,
                                'snippet': '',
                                'domain': self._extract_domain(href),
                                'result_type': self._determine_result_type(href, text, '')
                            })
                    except:
                        continue
                return results
            for idx, element in enumerate(result_elements[:10]):
                try:
                    result = self._extract_single_result(element, idx + 1)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Ошибка извлечения результата {idx + 1}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения результатов из DOM: {str(e)}")
        logger.info(f"📊 Извлечено {len(results)} результатов из DOM")
        return results

    def _extract_single_result(self, element, rank: int) -> Optional[Dict]:
        try:
            title_selectors = [
                'h2 a', 'h3 a', '.organic__title-wrapper a',
                '.serp-item__title a', '.title a', 'a[data-log-node="title"]',
                '.VanillaReact a', '.link'
            ]
            title = ""
            url = ""
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(
                        By.CSS_SELECTOR, selector)
                    if title_elem:
                        title = title_elem.text
                        url = title_elem.get_attribute('href') or ""
                        break
                except NoSuchElementException:
                    continue
            if not title:
                try:
                    link_elem = element.find_element(
                        By.CSS_SELECTOR, 'a[href]')
                    if link_elem:
                        title = link_elem.text or "Без заголовка"
                        url = link_elem.get_attribute('href') or ""
                except NoSuchElementException:
                    pass
            snippet_selectors = [
                '.organic__text', '.serp-item__text', '.snippet',
                '.text-container', '.organic__content', '.content',
                '.VanillaReact .text'
            ]
            snippet = ""
            for selector in snippet_selectors:
                try:
                    snippet_elem = element.find_element(
                        By.CSS_SELECTOR, selector)
                    if snippet_elem:
                        snippet = snippet_elem.text
                        break
                except NoSuchElementException:
                    continue
            if not snippet:
                snippet = element.text
                snippet = snippet[:200] + \
                    "..." if len(snippet) > 200 else snippet
            domain = self._extract_domain(url)
            result_type = self._determine_result_type(url, title, snippet)
            if title or url:
                return {
                    'rank': rank,
                    'title': title.strip(),
                    'url': url,
                    'snippet': snippet.strip(),
                    'domain': domain,
                    'result_type': result_type
                }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга результата {rank}: {str(e)}")
        return None

    def _extract_domain(self, url: str) -> str:
        """Извлечение домена из URL"""
        if not url:
            return ""
        try:
            import re
            # Простое извлечение домена без urllib
            match = re.search(r'https?://([^/]+)', url)
            return match.group(1) if match else ""
        except:
            return ""

    def _determine_result_type(self, url: str, title: str, snippet: str) -> str:
        """Определение типа результата поиска"""
        url_lower = url.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()

        # Проверяем по URL
        if 'yandex.ru/maps' in url_lower or 'maps.yandex' in url_lower:
            return 'maps_yandex'
        elif '2gis.ru' in url_lower or '2gis.com' in url_lower:
            return 'maps_2gis'
        elif any(domain in url_lower for domain in ['avito.ru', 'cian.ru', 'domclick.ru', 'youla.ru']):
            return 'realestate'
        elif any(domain in url_lower for domain in ['rosreestr.ru', 'gosuslugi.ru', 'egrp365.ru']):
            return 'government'
        elif 'wikipedia' in url_lower:
            return 'encyclopedia'

        # Проверяем по содержимому
        map_keywords = ['карт', 'map', 'координат', 'маршрут', 'навигац']
        if any(keyword in title_lower or keyword in snippet_lower for keyword in map_keywords):
            return 'maps_general'

        realestate_keywords = ['недвижим', 'квартир',
                               'дом', 'аренд', 'продаж', 'цена']
        if any(keyword in title_lower or keyword in snippet_lower for keyword in realestate_keywords):
            return 'realestate'

        return 'website'

    def _analyze_screenshot_with_ai(self, screenshot_path: Path, address: str) -> str:
        """Анализ скриншота с помощью локальной ИИ модели"""
        try:
            logger.info(
                f"🤖 Анализируем скриншот с помощью ИИ: {screenshot_path}")

            # Загружаем изображение
            image = cv2.imread(str(screenshot_path))
            if image is None:
                return "Ошибка загрузки изображения"

            # OCR извлечение текста
            ocr_text = self._extract_text_with_ocr(image)

            # Простой локальный анализ изображения
            height, width = image.shape[:2]

            analysis_parts = []
            analysis_parts.append(f"=== АНАЛИЗ СКРИНШОТА ===")
            analysis_parts.append(f"Адрес: {address}")
            analysis_parts.append(f"Размер изображения: {width}x{height}")
            analysis_parts.append(
                f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            analysis_parts.append("")

            # OCR текст
            if ocr_text:
                analysis_parts.append("=== ИЗВЛЕЧЕННЫЙ ТЕКСТ ===")
                analysis_parts.append(ocr_text)
                analysis_parts.append("")

                # Анализ OCR текста
                analysis_parts.append("=== АНАЛИЗ ТЕКСТА ===")

                # Ищем ключевые фразы
                text_lower = ocr_text.lower()

                if any(word in text_lower for word in ['найдено', 'результат', 'показано']):
                    analysis_parts.append("✅ Обнаружены результаты поиска")

                    # Пытаемся найти количество результатов
                    import re
                    numbers = re.findall(r'\d+', ocr_text)
                    if numbers:
                        analysis_parts.append(
                            f"📊 Числа в тексте: {', '.join(numbers[:5])}")

                if any(word in text_lower for word in ['карт', 'map', 'яндекс.карты']):
                    analysis_parts.append("🗺️ Найдены упоминания карт")

                if any(word in text_lower for word in ['капча', 'captcha', 'проверка']):
                    analysis_parts.append("🛡️ ВНИМАНИЕ: Обнаружена капча!")

                if 'ничего не найдено' in text_lower:
                    analysis_parts.append("❌ Результаты поиска отсутствуют")

                # Ищем адресные элементы
                address_words = address.lower().split()
                found_words = [word for word in address_words if len(
                    word) > 3 and word in text_lower]
                if found_words:
                    analysis_parts.append(
                        f"📍 Найдены слова адреса: {', '.join(found_words)}")

            else:
                analysis_parts.append(
                    "⚠️ Не удалось извлечь текст с помощью OCR")

            # Анализ изображения
            analysis_parts.append("")
            analysis_parts.append("=== АНАЛИЗ ИЗОБРАЖЕНИЯ ===")

            # Конвертируем в HSV для анализа цветов
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Ищем желтые элементы (характерные для Яндекса)
            yellow_lower = np.array([15, 100, 100])
            yellow_upper = np.array([35, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            yellow_pixels = cv2.countNonZero(yellow_mask)

            if yellow_pixels > 1000:
                analysis_parts.append(
                    "🟡 Обнаружены элементы интерфейса Яндекса")

            # Ищем синие ссылки
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            blue_pixels = cv2.countNonZero(blue_mask)

            if blue_pixels > 500:
                analysis_parts.append("🔗 Найдены элементы, похожие на ссылки")

            # Анализ структуры
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            large_rectangles = sum(
                1 for contour in contours if cv2.contourArea(contour) > 5000)

            if large_rectangles > 5:
                analysis_parts.append(
                    f"📋 Обнаружено {large_rectangles} крупных блоков контента")
            elif large_rectangles > 0:
                analysis_parts.append(
                    f"📋 Обнаружено {large_rectangles} блоков")
            else:
                analysis_parts.append("⚠️ Мало структурированного контента")

            # Проверка на капчу
            if self._detect_captcha_in_image(gray):
                analysis_parts.append("🛡️ ВНИМАНИЕ: Возможна капча!")

            return "\n".join(analysis_parts)

        except Exception as e:
            logger.error(f"❌ Ошибка ИИ анализа: {str(e)}")
            return f"Ошибка анализа изображения: {str(e)}"

    def _detect_captcha_in_image(self, gray_image) -> bool:
        """Простое определение капчи в изображении"""
        try:
            # Ищем характерные для капчи паттерны
            edges = cv2.Canny(gray_image, 100, 200)
            edge_density = cv2.countNonZero(
                edges) / (gray_image.shape[0] * gray_image.shape[1])

            # Искаженный текст (высокая вариация градиентов)
            sobel_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            gradient_variance = np.var(gradient_magnitude)

            # Эвристика: капча обычно имеет высокую плотность границ и вариацию градиентов
            if edge_density > 0.15 and gradient_variance > 2000:
                return True

        except Exception:
            pass

        return False

    def _extract_text_with_ocr(self, image) -> str:
        try:
            import easyocr
            try:
                reader = easyocr.Reader(['ru', 'en'], gpu=True)
            except Exception as gpu_error:
                logger.warning(
                    f"⚠️ EasyOCR не удалось инициализировать с GPU: {gpu_error}. Пробую CPU...")
                reader = easyocr.Reader(['ru', 'en'], gpu=False)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = reader.readtext(image_rgb, detail=0, paragraph=True)
            return "\n".join(result)
        except ImportError:
            logger.warning("⚠️ easyocr не установлен, OCR недоступен")
            return ""
        except Exception as e:
            logger.warning(f"⚠️ Ошибка OCR: {str(e)}")
            return ""

    def _analyze_page_text(self, page_text: str, address: str) -> str:
        """Анализ текста страницы"""
        try:
            analysis = []

            # Подсчет результатов
            result_patterns = [
                r'найдено[:\s]*(\d+)',
                r'показано[:\s]*(\d+)',
                r'результат[ов]*[:\s]*(\d+)',
                r'(\d+)[^\d]*результат'
            ]

            for pattern in result_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    analysis.append(
                        f"📊 Найдено упоминаний результатов: {matches[0]}")
                    break

            # Поиск ключевых слов
            if 'ничего не найдено' in page_text.lower():
                analysis.append("❌ Страница сообщает: ничего не найдено")
            elif any(word in page_text.lower() for word in ['карт', 'адрес', 'местоположение']):
                analysis.append("🗺️ Обнаружены упоминания карт/адресов")

            # Проверка на ошибки
            if any(word in page_text.lower() for word in ['ошибка', 'error', 'проблема']):
                analysis.append("⚠️ На странице есть упоминания ошибок")

            # Проверка на капчу
            if any(word in page_text.lower() for word in ['капча', 'captcha', 'проверка безопасности']):
                analysis.append(
                    "🛡️ Обнаружена капча или проверка безопасности")

            # Анализ адреса в тексте
            address_words = address.lower().split()
            found_words = sum(1 for word in address_words if len(
                word) > 3 and word in page_text.lower())
            if found_words > len(address_words) * 0.5:
                analysis.append(
                    f"✅ Большинство слов адреса найдено на странице ({found_words}/{len(address_words)})")

            analysis.append(f"📝 Общий объем текста: {len(page_text)} символов")

            return "\n".join(analysis)

        except Exception as e:
            return f"Ошибка анализа текста: {str(e)}"

    def _transliterate_russian(self, text: str) -> str:
        """Транслитерация русских символов на латинские"""
        transliteration_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y',
            'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E',
            'Ё': 'E', 'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
            'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh',
            'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        return ''.join(transliteration_dict.get(char, char) for char in text)


def run_local_browser_search(addresses: List[str], headless: bool = True, progress_callback=None) -> List[Dict]:
    """Запуск локального браузерного поиска (Selenium)"""
    import random
    agent = LocalBrowserAgent(headless=headless)
    try:
        agent.open()
        results = []
        for idx, address in enumerate(addresses):
            if progress_callback:
                progress_callback(idx, len(addresses), address)
            logger.info(f"🔍 Поиск {idx + 1}/{len(addresses)}: {address}")
            result = agent.search_address_in_yandex(address)
            results.append(result)
            if idx < len(addresses) - 1:
                time.sleep(random.randint(3, 6))
        return results
    finally:
        agent.close()
