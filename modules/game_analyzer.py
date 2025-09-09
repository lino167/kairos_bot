#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Módulo de Análise Individual de Jogos
Analisa cada jogo individualmente extraindo dados detalhados das páginas específicas
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import async_playwright

from config.settings import (
    BASE_URL, PLAYWRIGHT_CONFIG, TIMEOUTS, SELECTORS,
    EXTRACTION_CONFIG, FILE_CONFIG, FILE_PATTERNS,
    DATA_CONFIG, MESSAGES, DATA_DIR
)
from utils.logger import get_logger
from utils.helpers import format_timestamp

class GameAnalyzer:
    """Classe responsável pela análise detalhada de jogos individuais"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.browser = None
        self.page = None
        self.analyzed_games = []
        self.stats = {
            'total_analyzed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'tables_found': 0,
            'data_points_extracted': 0
        }
    
    async def setup_browser(self):
        """Configura o navegador Playwright"""
        self.logger.info("🔧 Configurando navegador para análise individual...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=PLAYWRIGHT_CONFIG['headless'],
            args=PLAYWRIGHT_CONFIG['args']
        )
        
        context = await self.browser.new_context(
            viewport=PLAYWRIGHT_CONFIG['viewport'],
            user_agent=PLAYWRIGHT_CONFIG['user_agent']
        )
        
        self.page = await context.new_page()
        self.logger.info("✅ Navegador configurado para análise individual")
    
    async def analyze_game_from_url(self, game_url, game_info=None):
        """Analisa um jogo específico a partir de sua URL
        
        Args:
            game_url (str): URL do jogo para análise
            game_info (dict): Informações básicas do jogo (opcional)
            
        Returns:
            dict: Dados detalhados do jogo analisado
        """
        self.logger.info(f"🎯 Analisando jogo: {game_url}")
        
        try:
            # Navega para a página do jogo
            await self.page.goto(
                game_url,
                wait_until=PLAYWRIGHT_CONFIG['wait_until'],
                timeout=TIMEOUTS['page_load']
            )
            
            # Aguarda o carregamento da página
            await self.page.wait_for_timeout(2000)
            
            # Extrai informações básicas do jogo
            game_data = await self._extract_game_basic_info(game_url, game_info)
            
            # Extrai dados das tabelas de apostas
            betting_tables = await self._extract_betting_tables()
            game_data['betting_tables'] = betting_tables
            
            # Extrai histórico de movimentação
            movement_history = await self._extract_movement_history()
            game_data['movement_history'] = movement_history
            
            # Extrai estatísticas adicionais
            additional_stats = await self._extract_additional_stats()
            game_data['additional_stats'] = additional_stats
            
            # Calcula métricas de análise
            game_data['analysis_metrics'] = self._calculate_analysis_metrics(game_data)
            
            self.stats['successful_extractions'] += 1
            self.stats['data_points_extracted'] += len(game_data.get('betting_tables', {}))
            
            self.logger.info(f"✅ Jogo analisado com sucesso: {game_data.get('teams', 'N/A')}")
            return game_data
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao analisar jogo {game_url}: {e}")
            self.stats['failed_extractions'] += 1
            return None
    
    async def _extract_game_basic_info(self, game_url, game_info=None):
        """Extrai informações básicas do jogo"""
        game_data = {
            'url': game_url,
            'extraction_timestamp': datetime.now().isoformat(),
            'game_id': self._extract_game_id_from_url(game_url)
        }
        
        # Se temos informações básicas, as incluímos
        if game_info:
            game_data.update(game_info)
        
        try:
            # Tenta extrair título da página
            title = await self.page.title()
            if title:
                game_data['page_title'] = title
                # Extrai times do título se não temos essa informação
                if 'teams' not in game_data and ' - ' in title:
                    game_data['teams'] = title.split(' - ')[0] + ' - ' + title.split(' - ')[1]
            
            # Extrai informações do cabeçalho do jogo
            header_info = await self._extract_header_info()
            if header_info:
                game_data.update(header_info)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao extrair informações básicas: {e}")
        
        return game_data
    
    async def _extract_header_info(self):
        """Extrai informações do cabeçalho da página do jogo"""
        header_info = {}
        
        try:
            # Possíveis seletores para informações do cabeçalho
            header_selectors = [
                'h1', 'h2', '.game-title', '.match-title',
                '.teams', '.game-info', '.match-info'
            ]
            
            for selector in header_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip():
                        if selector in ['h1', 'h2', '.game-title', '.match-title']:
                            header_info['title'] = text.strip()
                        elif 'team' in selector.lower():
                            header_info['teams_header'] = text.strip()
                        
        except Exception as e:
            self.logger.debug(f"Erro ao extrair header: {e}")
        
        return header_info
    
    async def _extract_betting_tables(self):
        """Extrai dados das tabelas de apostas disponíveis"""
        betting_tables = {}
        
        try:
            # Procura por tabelas na página
            tables = await self.page.query_selector_all('table')
            self.logger.info(f"📊 Encontradas {len(tables)} tabelas na página")
            
            for i, table in enumerate(tables):
                table_data = await self._extract_table_data(table, f"table_{i+1}")
                if table_data:
                    betting_tables[f"table_{i+1}"] = table_data
                    self.stats['tables_found'] += 1
            
            # Procura especificamente pelas tabelas de "No" e "Yes"
            no_yes_tables = await self._extract_no_yes_tables()
            if no_yes_tables:
                betting_tables.update(no_yes_tables)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair tabelas de apostas: {e}")
        
        return betting_tables
    
    async def _extract_table_data(self, table, table_name):
        """Extrai dados de uma tabela específica"""
        try:
            # Extrai cabeçalhos
            headers = []
            header_rows = await table.query_selector_all('thead tr, tr:first-child')
            if header_rows:
                header_cells = await header_rows[0].query_selector_all('th, td')
                for cell in header_cells:
                    text = await cell.text_content()
                    headers.append(text.strip() if text else '')
            
            # Extrai dados das linhas
            rows_data = []
            data_rows = await table.query_selector_all('tbody tr, tr:not(:first-child)')
            
            for row in data_rows:
                cells = await row.query_selector_all('td, th')
                row_data = []
                for cell in cells:
                    text = await cell.text_content()
                    row_data.append(text.strip() if text else '')
                
                if row_data and any(cell for cell in row_data):  # Só adiciona se não estiver vazia
                    rows_data.append(row_data)
            
            if headers or rows_data:
                return {
                    'name': table_name,
                    'headers': headers,
                    'rows': rows_data,
                    'row_count': len(rows_data),
                    'column_count': len(headers) if headers else (len(rows_data[0]) if rows_data else 0)
                }
                
        except Exception as e:
            self.logger.debug(f"Erro ao extrair dados da tabela {table_name}: {e}")
        
        return None
    
    async def _extract_no_yes_tables(self):
        """Extrai especificamente as tabelas de 'No' e 'Yes' como no exemplo fornecido"""
        no_yes_data = {}
        
        try:
            # Procura por elementos que contenham "No" e "Yes" com valores monetários
            # Baseado no exemplo: "281€ - 2.44" para No e "82€ - 1.69" para Yes
            
            # Padrão para encontrar valores monetários e odds
            money_pattern = r'(\d+)€\s*-\s*([\d.]+)'
            
            # Procura por todos os elementos de texto na página
            all_elements = await self.page.query_selector_all('*')
            
            no_data = []
            yes_data = []
            
            for element in all_elements:
                text = await element.text_content()
                if text and text.strip():
                    text = text.strip()
                    
                    # Verifica se contém padrão de dinheiro e odds
                    money_match = re.search(money_pattern, text)
                    if money_match:
                        money_value = money_match.group(1)
                        odds_value = money_match.group(2)
                        
                        # Determina se é "No" ou "Yes" baseado no contexto
                        parent_text = await element.evaluate('el => el.parentElement ? el.parentElement.textContent : ""')
                        
                        if 'no' in text.lower() or 'no' in parent_text.lower():
                            no_data.append({
                                'money': f"{money_value}€",
                                'odds': odds_value,
                                'full_text': text
                            })
                        elif 'yes' in text.lower() or 'yes' in parent_text.lower():
                            yes_data.append({
                                'money': f"{money_value}€",
                                'odds': odds_value,
                                'full_text': text
                            })
            
            if no_data:
                no_yes_data['no_bets'] = no_data
            if yes_data:
                no_yes_data['yes_bets'] = yes_data
                
        except Exception as e:
            self.logger.debug(f"Erro ao extrair tabelas No/Yes: {e}")
        
        return no_yes_data
    
    async def _extract_movement_history(self):
        """Extrai histórico de movimentação das apostas"""
        movement_data = []
        
        try:
            # Procura por tabelas que contenham dados temporais
            # Baseado no exemplo que mostra horários como "15:18 09.09"
            time_pattern = r'(\d{1,2}:\d{2}\s+\d{1,2}\.\d{2})'
            
            tables = await self.page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_text = []
                    
                    for cell in cells:
                        text = await cell.text_content()
                        if text:
                            row_text.append(text.strip())
                    
                    # Verifica se a linha contém dados temporais
                    full_row_text = ' '.join(row_text)
                    if re.search(time_pattern, full_row_text):
                        movement_data.append({
                            'timestamp_extracted': datetime.now().isoformat(),
                            'row_data': row_text,
                            'full_text': full_row_text
                        })
                        
        except Exception as e:
            self.logger.debug(f"Erro ao extrair histórico de movimentação: {e}")
        
        return movement_data
    
    async def _extract_additional_stats(self):
        """Extrai estatísticas adicionais da página"""
        stats = {}
        
        try:
            # Conta elementos específicos
            stats['total_tables'] = len(await self.page.query_selector_all('table'))
            stats['total_links'] = len(await self.page.query_selector_all('a'))
            stats['page_load_time'] = datetime.now().isoformat()
            
            # Extrai meta informações
            meta_elements = await self.page.query_selector_all('meta')
            meta_info = {}
            
            for meta in meta_elements:
                name = await meta.get_attribute('name')
                content = await meta.get_attribute('content')
                if name and content:
                    meta_info[name] = content
            
            if meta_info:
                stats['meta_info'] = meta_info
                
        except Exception as e:
            self.logger.debug(f"Erro ao extrair estatísticas adicionais: {e}")
        
        return stats
    
    def _calculate_analysis_metrics(self, game_data):
        """Calcula métricas de análise do jogo"""
        metrics = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_completeness_score': 0,
            'betting_activity_level': 'unknown',
            'data_quality_indicators': []
        }
        
        try:
            # Calcula score de completude dos dados
            completeness_factors = [
                'teams' in game_data,
                'betting_tables' in game_data and game_data['betting_tables'],
                'movement_history' in game_data and game_data['movement_history'],
                'page_title' in game_data
            ]
            
            metrics['data_completeness_score'] = sum(completeness_factors) / len(completeness_factors)
            
            # Avalia nível de atividade de apostas
            betting_tables = game_data.get('betting_tables', {})
            if betting_tables:
                total_rows = sum(table.get('row_count', 0) for table in betting_tables.values() if isinstance(table, dict))
                if total_rows > 20:
                    metrics['betting_activity_level'] = 'high'
                elif total_rows > 10:
                    metrics['betting_activity_level'] = 'medium'
                else:
                    metrics['betting_activity_level'] = 'low'
            
            # Indicadores de qualidade
            if game_data.get('teams'):
                metrics['data_quality_indicators'].append('teams_identified')
            if betting_tables:
                metrics['data_quality_indicators'].append('betting_data_available')
            if game_data.get('movement_history'):
                metrics['data_quality_indicators'].append('historical_data_available')
                
        except Exception as e:
            self.logger.debug(f"Erro ao calcular métricas: {e}")
        
        return metrics
    
    def _extract_game_id_from_url(self, url):
        """Extrai o ID do jogo da URL"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            return query_params.get('id', [None])[0]
        except:
            return None
    
    async def analyze_multiple_games(self, game_urls_or_data):
        """Analisa múltiplos jogos
        
        Args:
            game_urls_or_data: Lista de URLs ou dicionários com dados dos jogos
        """
        self.logger.info(f"🎯 Iniciando análise de {len(game_urls_or_data)} jogos")
        
        for i, game_item in enumerate(game_urls_or_data):
            try:
                if isinstance(game_item, str):
                    # É uma URL
                    game_url = game_item
                    game_info = None
                else:
                    # É um dicionário com dados
                    game_url = game_item.get('game_link') or game_item.get('url')
                    game_info = game_item
                
                if not game_url:
                    self.logger.warning(f"⚠️ Jogo {i+1}: URL não encontrada")
                    continue
                
                self.logger.info(f"📊 Analisando jogo {i+1}/{len(game_urls_or_data)}")
                
                analyzed_game = await self.analyze_game_from_url(game_url, game_info)
                if analyzed_game:
                    self.analyzed_games.append(analyzed_game)
                
                self.stats['total_analyzed'] += 1
                
                # Pausa entre análises para não sobrecarregar o servidor
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao processar jogo {i+1}: {e}")
        
        self.logger.info(f"✅ Análise concluída: {len(self.analyzed_games)} jogos analisados com sucesso")
    
    async def save_analysis_results(self):
        """Salva os resultados da análise"""
        if not self.analyzed_games:
            self.logger.warning("⚠️ Nenhum jogo analisado para salvar")
            return
        
        timestamp = format_timestamp()
        
        # Salva dados detalhados
        detailed_file = DATA_DIR / f"detailed_analysis_{timestamp}.json"
        
        analysis_data = {
            'extraction_info': {
                'timestamp': datetime.now().isoformat(),
                'total_games_analyzed': len(self.analyzed_games),
                'statistics': self.stats
            },
            'games': self.analyzed_games
        }
        
        try:
            with open(detailed_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Análise detalhada salva: {detailed_file}")
            
            # Salva resumo
            summary_file = DATA_DIR / f"analysis_summary_{timestamp}.json"
            summary_data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': self.stats,
                'games_summary': [
                    {
                        'game_id': game.get('game_id'),
                        'teams': game.get('teams'),
                        'url': game.get('url'),
                        'tables_found': len(game.get('betting_tables', {})),
                        'data_completeness': game.get('analysis_metrics', {}).get('data_completeness_score', 0)
                    }
                    for game in self.analyzed_games
                ]
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📋 Resumo da análise salvo: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar resultados: {e}")
    
    def print_analysis_summary(self):
        """Imprime resumo da análise"""
        print("\n" + "="*60)
        print("📊 RESUMO DA ANÁLISE INDIVIDUAL DE JOGOS")
        print("="*60)
        print(f"🎯 Total de jogos analisados: {self.stats['total_analyzed']}")
        print(f"✅ Extrações bem-sucedidas: {self.stats['successful_extractions']}")
        print(f"❌ Extrações falharam: {self.stats['failed_extractions']}")
        print(f"📊 Tabelas encontradas: {self.stats['tables_found']}")
        print(f"📈 Pontos de dados extraídos: {self.stats['data_points_extracted']}")
        
        if self.analyzed_games:
            print(f"\n🎮 JOGOS ANALISADOS:")
            for i, game in enumerate(self.analyzed_games[:5], 1):  # Mostra apenas os primeiros 5
                teams = game.get('teams', 'N/A')
                tables_count = len(game.get('betting_tables', {}))
                completeness = game.get('analysis_metrics', {}).get('data_completeness_score', 0)
                print(f"  {i}. {teams} - {tables_count} tabelas - {completeness:.1%} completo")
            
            if len(self.analyzed_games) > 5:
                print(f"  ... e mais {len(self.analyzed_games) - 5} jogos")
        
        print("="*60)
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.browser:
            await self.browser.close()
            self.logger.info("🧹 Navegador fechado")

# Função de conveniência para análise rápida
async def analyze_single_game(game_url, save_results=True):
    """Analisa um único jogo
    
    Args:
        game_url (str): URL do jogo para análise
        save_results (bool): Se deve salvar os resultados
    
    Returns:
        dict: Dados do jogo analisado
    """
    analyzer = GameAnalyzer()
    
    try:
        await analyzer.setup_browser()
        game_data = await analyzer.analyze_game_from_url(game_url)
        
        if game_data and save_results:
            analyzer.analyzed_games = [game_data]
            await analyzer.save_analysis_results()
        
        return game_data
        
    finally:
        await analyzer.cleanup()

# Exemplo de uso
if __name__ == "__main__":
    # Exemplo com a URL fornecida
    example_url = "https://www.excapper.com/?action=game&id=34705909"
    
    async def main():
        result = await analyze_single_game(example_url)
        if result:
            print(f"\n✅ Jogo analisado: {result.get('teams', 'N/A')}")
            print(f"📊 Tabelas encontradas: {len(result.get('betting_tables', {}))}")
            print(f"📈 Histórico: {len(result.get('movement_history', []))} entradas")
        else:
            print("❌ Falha na análise do jogo")
    
    asyncio.run(main())