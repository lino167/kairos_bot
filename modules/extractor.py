#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Módulo de Extração
Extrai dados dos jogos do site Excapper
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright

from config.settings import (
    BASE_URL, PLAYWRIGHT_CONFIG, TIMEOUTS, SELECTORS,
    EXTRACTION_CONFIG, FILE_CONFIG, FILE_PATTERNS,
    DATA_CONFIG, MESSAGES, DATA_DIR, SCREENSHOTS_DIR
)
from utils.logger import get_logger
from utils.helpers import format_timestamp, validate_game_data

class GameExtractor:
    """Classe responsável pela extração de dados dos jogos"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.browser = None
        self.page = None
        self.games_data = []
        self.stats = {}
    
    async def setup_browser(self):
        """Configura o navegador Playwright"""
        self.logger.info(MESSAGES['browser_setup'])
        
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
        self.logger.info("✅ Navegador configurado com sucesso")
    
    async def navigate_to_site(self):
        """Navega para o site principal"""
        self.logger.info(MESSAGES['navigation'].format(url=BASE_URL))
        
        await self.page.goto(
            BASE_URL, 
            wait_until=PLAYWRIGHT_CONFIG['wait_until'],
            timeout=TIMEOUTS['page_load']
        )
        
        # Aguarda o carregamento das tabelas
        await self.page.wait_for_selector(
            SELECTORS['tables'], 
            timeout=TIMEOUTS['element_wait']
        )
        
        self.logger.info("✅ Página carregada com sucesso")
    
    async def extract_games_data(self):
        """Extrai dados de todos os jogos"""
        self.logger.info(MESSAGES['extraction_start'])
        
        # Encontra todas as linhas de jogos
        game_rows = await self.page.query_selector_all(SELECTORS['game_rows'])
        total_games = len(game_rows)
        
        self.logger.info(f"🎯 Encontradas {total_games} linhas de jogos")
        
        # Limita o número de jogos se configurado
        max_games = EXTRACTION_CONFIG.get('max_games_per_run', total_games)
        if total_games > max_games:
            game_rows = game_rows[:max_games]
            self.logger.warning(f"⚠️ Limitando extração a {max_games} jogos")
        
        # Extrai dados de cada jogo
        for i, row in enumerate(game_rows):
            try:
                game_data = await self._extract_single_game(row, i)
                if game_data and validate_game_data(game_data):
                    self.games_data.append(game_data)
                    self.logger.debug(f"✅ Jogo {i+1}/{len(game_rows)}: {game_data['teams']}")
                else:
                    self.logger.warning(f"⚠️ Dados inválidos para jogo {i+1}")
            except Exception as e:
                self.logger.error(f"❌ Erro ao extrair jogo {i+1}: {e}")
        
        self.logger.info(MESSAGES['extraction_complete'].format(count=len(self.games_data)))
    
    async def _extract_single_game(self, row, index):
        """Extrai dados de um único jogo"""
        # Extrai atributos da linha
        game_id = await row.get_attribute('game_id')
        data_game_link = await row.get_attribute('data-game-link')
        
        # Extrai dados das células
        cells = await row.query_selector_all(SELECTORS['game_cells'])
        
        if len(cells) < 5:
            return None
        
        # Extrai texto de cada célula
        date_time = await cells[0].inner_text()
        
        # Extrai informações do país
        country_info = await self._extract_country_info(cells[1])
        
        league = await cells[2].inner_text()
        teams = await cells[3].inner_text()
        money = await cells[4].inner_text()
        
        # Processa o link do jogo
        game_link = self._process_game_link(data_game_link)
        
        # Monta dados do jogo
        game_data = {
            'index': index + 1,
            'game_id': game_id,
            'date_time': date_time.strip(),
            'country': country_info,
            'league': league.strip(),
            'teams': teams.strip(),
            'money': money.strip(),
            'game_link': game_link,
            'data_game_link_raw': data_game_link,
            'extracted_at': datetime.now().isoformat()
        }
        
        # Processa informações adicionais
        self._process_additional_info(game_data)
        
        return game_data
    
    async def _extract_country_info(self, cell):
        """Extrai informações do país da célula"""
        country_img = await cell.query_selector(SELECTORS['country_img'])
        if country_img:
            return {
                'src': await country_img.get_attribute('src'),
                'alt': await country_img.get_attribute('alt'),
                'title': await country_img.get_attribute('title')
            }
        return {}
    
    def _process_game_link(self, data_game_link):
        """Processa o link do jogo"""
        if data_game_link:
            clean_link = data_game_link.replace('&amp;', '&')
            return urljoin(BASE_URL, clean_link.strip())
        return None
    
    def _process_additional_info(self, game_data):
        """Processa informações adicionais do jogo"""
        teams = game_data['teams']
        money = game_data['money']
        
        # Separa times casa e visitante
        if ' - ' in teams:
            team_parts = teams.split(' - ')
            game_data['home_team'] = team_parts[0].strip()
            game_data['away_team'] = team_parts[1].strip()
        
        # Extrai valor monetário numérico
        money_match = re.search(r'([0-9,]+)\s*€', money)
        if money_match:
            money_value = money_match.group(1).replace(',', '')
            try:
                game_data['money_numeric'] = int(money_value)
            except ValueError:
                game_data['money_numeric'] = 0
        else:
            game_data['money_numeric'] = 0
    
    async def validate_sample_links(self):
        """Valida uma amostra de links extraídos"""
        sample_size = EXTRACTION_CONFIG['validate_links_sample']
        self.logger.info(MESSAGES['validation_start'])
        
        valid_links = 0
        sample_games = self.games_data[:sample_size]
        
        for i, game in enumerate(sample_games):
            if game.get('game_link'):
                try:
                    self.logger.debug(f"🌐 Testando link {i+1}: {game['game_link']}")
                    response = await self.page.goto(
                        game['game_link'], 
                        timeout=TIMEOUTS['page_load']
                    )
                    if response.status == 200:
                        valid_links += 1
                        self.logger.debug(f"✅ Link válido: {game['teams']}")
                    else:
                        self.logger.warning(f"⚠️ Link retornou status {response.status}: {game['teams']}")
                except Exception as e:
                    self.logger.error(f"❌ Erro ao acessar link: {e}")
        
        self.logger.info(f"📊 Links válidos: {valid_links}/{sample_size}")
        return valid_links
    
    def generate_statistics(self):
        """Gera estatísticas dos dados extraídos"""
        if not self.games_data:
            return {}
        
        self.stats = {
            'total_games': len(self.games_data),
            'games_with_links': sum(1 for game in self.games_data if game.get('game_link')),
            'games_with_money': sum(1 for game in self.games_data if game.get('money_numeric', 0) > 0),
            'total_money': sum(game.get('money_numeric', 0) for game in self.games_data),
            'leagues': list(set(game['league'] for game in self.games_data if game.get('league'))),
            'countries': list(set(
                game['country'].get('alt', '') 
                for game in self.games_data 
                if game.get('country', {}).get('alt')
            )),
            'date_range': {
                'first': self.games_data[0]['date_time'] if self.games_data else None,
                'last': self.games_data[-1]['date_time'] if self.games_data else None
            },
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        return self.stats
    
    async def save_screenshots(self):
        """Salva screenshots da página"""
        if not EXTRACTION_CONFIG['save_screenshots']:
            return
        
        timestamp = format_timestamp()
        
        try:
            # Screenshot da página completa
            full_path = SCREENSHOTS_DIR / FILE_PATTERNS['screenshot_full'].format(timestamp=timestamp)
            await self.page.screenshot(
                path=str(full_path), 
                full_page=True,
                timeout=TIMEOUTS['screenshot']
            )
            
            # Screenshot do viewport
            viewport_path = SCREENSHOTS_DIR / FILE_PATTERNS['screenshot_viewport'].format(timestamp=timestamp)
            await self.page.screenshot(
                path=str(viewport_path),
                timeout=TIMEOUTS['screenshot']
            )
            
            self.logger.info(f"📸 Screenshots salvos: {full_path.name}, {viewport_path.name}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar screenshots: {e}")
    
    async def save_results(self):
        """Salva os resultados em arquivo JSON"""
        timestamp = format_timestamp()
        filename = FILE_PATTERNS['games_data'].format(timestamp=timestamp)
        filepath = DATA_DIR / filename
        
        results = {
            'metadata': {
                'extraction_timestamp': datetime.now().isoformat(),
                'base_url': BASE_URL,
                'total_games_extracted': len(self.games_data),
                'extractor_version': '2.0',
                'config_used': {
                    'max_games': EXTRACTION_CONFIG.get('max_games_per_run'),
                    'validate_sample': EXTRACTION_CONFIG['validate_links_sample']
                }
            },
            'statistics': self.stats,
            'games': self.games_data
        }
        
        with open(filepath, 'w', encoding=FILE_CONFIG['encoding']) as f:
            json.dump(
                results, f, 
                indent=FILE_CONFIG['json_indent'],
                ensure_ascii=FILE_CONFIG['ensure_ascii']
            )
        
        self.logger.info(MESSAGES['save_data'].format(filename=filename))
        return str(filepath)
    
    def print_summary(self):
        """Imprime resumo dos dados extraídos"""
        if not self.stats:
            self.generate_statistics()
        
        print("\n" + "="*60)
        print("RESUMO DA EXTRAÇÃO DE DADOS DOS JOGOS")
        print("="*60)
        
        print(f"🎯 Total de jogos: {self.stats['total_games']}")
        print(f"🔗 Jogos com links: {self.stats['games_with_links']}")
        print(f"💰 Jogos com valores: {self.stats['games_with_money']}")
        print(f"💵 Valor total: {self.stats['total_money']:,} €")
        print(f"🏆 Ligas únicas: {len(self.stats['leagues'])}")
        print(f"🌍 Países únicos: {len(self.stats['countries'])}")
        
        # Mostra exemplos
        if self.games_data:
            print(f"\n🎮 Exemplos de jogos extraídos:")
            for i, game in enumerate(self.games_data[:3]):
                print(f"   {i+1}. {game['teams']} ({game['league']})")
                print(f"      🔗 Link: {game['game_link']}")
                print(f"      💰 Valor: {game['money']}")
    
    async def cleanup(self):
        """Limpa recursos do navegador"""
        if self.browser:
            await self.browser.close()
            self.logger.info(MESSAGES['cleanup'])
    
    async def run_extraction(self):
        """Executa o processo completo de extração"""
        self.logger.info(MESSAGES['start'])
        
        try:
            await self.setup_browser()
            await self.navigate_to_site()
            await self.extract_games_data()
            
            if self.games_data:
                await self.validate_sample_links()
                self.generate_statistics()
                
                if EXTRACTION_CONFIG['save_screenshots']:
                    await self.save_screenshots()
                
                filepath = await self.save_results()
                self.print_summary()
                
                self.logger.info(f"✅ Extração concluída: {filepath}")
                return filepath
            else:
                self.logger.error("❌ Nenhum dado de jogo foi extraído")
                return None
        
        except Exception as e:
            self.logger.error(MESSAGES['error'].format(error=e))
            raise
        
        finally:
            await self.cleanup()

# Função de conveniência para uso direto
async def extract_games():
    """Função de conveniência para extrair jogos"""
    extractor = GameExtractor()
    return await extractor.run_extraction()

if __name__ == "__main__":
    asyncio.run(extract_games())