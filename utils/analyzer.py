import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple
from collections import Counter


class ResultAnalyzer:
    def __init__(self, results_df: pd.DataFrame):
        self.df = results_df

    def get_domain_distribution(self) -> pd.DataFrame:
        """Распределение результатов по доменам"""
        domain_counts = self.df['domain'].value_counts()
        return pd.DataFrame({
            'domain': domain_counts.index,
            'count': domain_counts.values,
            'percentage': (domain_counts.values / len(self.df) * 100).round(2)
        })

    def get_result_type_distribution(self) -> pd.DataFrame:
        """Распределение по типам результатов"""
        type_counts = self.df['result_type'].value_counts()
        type_names = {
            'maps': 'Карты',
            'maps_2gis': 'Карты 2GIS',
            'realestate': 'Недвижимость',
            'government': 'Госсайты',
            'encyclopedia': 'Энциклопедии',
            'website': 'Веб-сайты'
        }

        return pd.DataFrame({
            'type': [type_names.get(t, t) for t in type_counts.index],
            'count': type_counts.values,
            'percentage': (type_counts.values / len(self.df) * 100).round(2)
        })

    def calculate_relevance_stats(self) -> Dict:
        """Статистика релевантности результатов"""
        stats = {
            'total_results': len(self.df),
            'unique_addresses': self.df['address'].nunique(),
            'avg_results_per_address': len(self.df) / self.df['address'].nunique() if self.df['address'].nunique() > 0 else 0,
            'top_positions_maps': len(self.df[(self.df['rank'] <= 3) & (self.df['result_type'].isin(['maps', 'maps_2gis']))]),
            'addresses_with_maps': self.df[self.df['result_type'].isin(['maps', 'maps_2gis'])]['address'].nunique()
        }

        # Процент адресов с картами в топ-3
        if stats['unique_addresses'] > 0:
            stats['maps_coverage_percent'] = (
                stats['addresses_with_maps'] / stats['unique_addresses'] * 100)
        else:
            stats['maps_coverage_percent'] = 0

        return stats

    def create_domain_pie_chart(self) -> go.Figure:
        """Круговая диаграмма распределения по доменам"""
        domain_dist = self.get_domain_distribution()

        # Группируем малые домены
        threshold = 2  # процент
        major_domains = domain_dist[domain_dist['percentage'] >= threshold]
        minor_domains = domain_dist[domain_dist['percentage'] < threshold]

        if not minor_domains.empty:
            other_row = pd.DataFrame({
                'domain': ['Другие'],
                'count': [minor_domains['count'].sum()],
                'percentage': [minor_domains['percentage'].sum()]
            })
            plot_data = pd.concat(
                [major_domains, other_row], ignore_index=True)
        else:
            plot_data = major_domains

        fig = px.pie(
            plot_data,
            values='count',
            names='domain',
            title='Распределение результатов по доменам',
            hole=0.3
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Количество: %{value}<br>Процент: %{percent}<extra></extra>'
        )

        return fig

    def create_type_bar_chart(self) -> go.Figure:
        """Гистограмма типов результатов"""
        type_dist = self.get_result_type_distribution()

        fig = px.bar(
            type_dist,
            x='type',
            y='count',
            title='Распределение по типам результатов',
            labels={'type': 'Тип результата', 'count': 'Количество'},
            text='count'
        )

        fig.update_traces(
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Количество: %{y}<br>Процент: %{customdata:.1f}%<extra></extra>',
            customdata=type_dist['percentage']
        )

        fig.update_layout(
            showlegend=False,
            yaxis_title='Количество результатов',
            xaxis_title='Тип результата'
        )

        return fig

    def create_top_domains_chart(self, top_n: int = 10) -> go.Figure:
        """График топ доменов"""
        domain_counts = self.df['domain'].value_counts().head(top_n)

        fig = go.Figure([go.Bar(
            x=domain_counts.values,
            y=domain_counts.index,
            orientation='h',
            text=domain_counts.values,
            textposition='auto',
            marker_color='lightblue'
        )])

        fig.update_layout(
            title=f'Топ-{top_n} доменов по частоте',
            xaxis_title='Количество результатов',
            yaxis_title='Домен',
            height=400,
            margin=dict(l=150)
        )

        return fig

    def get_addresses_without_maps(self) -> List[str]:
        """Получить адреса без результатов на картах"""
        addresses_with_maps = set(
            self.df[self.df['result_type'].isin(
                ['maps', 'maps_2gis'])]['address']
        )
        all_addresses = set(self.df['address'])
        return list(all_addresses - addresses_with_maps)

    def get_position_analysis(self) -> pd.DataFrame:
        """Анализ позиций результатов"""
        position_stats = []

        for result_type in self.df['result_type'].unique():
            type_df = self.df[self.df['result_type'] == result_type]
            stats = {
                'type': result_type,
                'avg_position': type_df['rank'].mean(),
                'min_position': type_df['rank'].min(),
                'max_position': type_df['rank'].max(),
                'count': len(type_df)
            }
            position_stats.append(stats)

        return pd.DataFrame(position_stats).sort_values('avg_position')
