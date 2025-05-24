import json
import pandas as pd
from typing import List, Dict, Optional
import re


class DataProcessor:
    @staticmethod
    def load_json_file(file) -> List[Dict]:
        """Загрузка и парсинг JSON файла"""
        try:
            content = file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            data = json.loads(content)

            # Проверяем, что это массив объектов
            if not isinstance(data, list):
                raise ValueError("JSON должен содержать массив объектов")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Ошибка загрузки файла: {str(e)}")

    @staticmethod
    def parse_json_text(text: str) -> List[Dict]:
        """Парсинг JSON из текстового поля"""
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("JSON должен содержать массив объектов")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {str(e)}")

    @staticmethod
    def extract_addresses(data: List[Dict]) -> List[str]:
        """Извлечение адресов из данных"""
        addresses = []
        for item in data:
            if isinstance(item, dict) and 'address' in item:
                address = item['address']
                if address and isinstance(address, str):
                    # Нормализуем адрес
                    address = DataProcessor.normalize_address(address)
                    addresses.append(address)
        return addresses

    @staticmethod
    def normalize_address(address: str) -> str:
        """Нормализация адреса для поиска"""
        # Убираем лишние пробелы
        address = ' '.join(address.split())

        # Заменяем сокращения
        replacements = {
            ' д. ': ' дом ',
            ' д ': ' дом ',
            ' кв. ': ' квартира ',
            ' кв ': ' квартира ',
            ' ул. ': ' улица ',
            ' ул ': ' улица ',
            ' пер. ': ' переулок ',
            ' пер ': ' переулок ',
            ' пр-т ': ' проспект ',
            ' пр-кт ': ' проспект ',
            ' р-н ': ' район ',
            ' обл. ': ' область ',
            ' обл ': ' область ',
            ' г. ': ' город ',
            ' г ': ' город ',
            ' ст-ца ': ' станица ',
            ' с. ': ' село ',
            ' с ': ' село ',
            ' пос. ': ' поселок ',
            ' пос ': ' поселок ',
        }

        for old, new in replacements.items():
            address = address.replace(old, new)

        return address

    @staticmethod
    def results_to_dataframe(results: List[Dict]) -> pd.DataFrame:
        """Преобразование результатов в DataFrame"""
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Упорядочиваем колонки
        columns_order = ['address', 'rank', 'title', 'domain', 'result_type',
                         'snippet', 'additional_info', 'url']

        # Проверяем наличие всех колонок
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''

        return df[columns_order]

    @staticmethod
    def save_to_csv(df: pd.DataFrame, filename: str = 'search_results.csv'):
        """Сохранение DataFrame в CSV"""
        df.to_csv(filename, index=False, encoding='utf-8-sig')

    @staticmethod
    def save_to_excel(df: pd.DataFrame, filename: str = 'search_results.xlsx'):
        """Сохранение DataFrame в Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Результаты поиска', index=False)

            # Автоматическая настройка ширины колонок
            worksheet = writer.sheets['Результаты поиска']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                # Ограничиваем максимальную ширину
                max_length = min(max_length, 50)
                worksheet.column_dimensions[chr(
                    65 + idx)].width = max_length + 2
