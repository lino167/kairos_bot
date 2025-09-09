#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Módulo de Investigação
Investiga jogos individuais e coleta dados detalhados
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from config.settings import (
    BASE_URL, PLAYWRIGHT_CONFIG, TIMEOUTS, SELECTORS,
    INVESTIGATION_CONFIG, FILE_PATTERNS, DATA_DIR
)
from utils.logger import get_logger, LogContext
from utils.helpers import (
    format_timestamp, validate_url, load_json_file,
    save_json_file, generate_game_hash
)

class GameInvestigator:
    """Classe responsável pela investigação detalhada de jogos"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.browser = None
        self.page = None
        self.investigated_games = []
        self.failed_investigations = []
    
    async def setup_browser(self):
        """Configura o navegador Playwright"""
        with LogContext(self.logger, "Configuração do navegador"):
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
    
    async def investigate_game(self, game_data):
        """Investiga um jogo específico"""
        game_link = game_data.get('game_link')
        game_teams = game_data.get('teams', 'Jogo desconhecido')
        
        if not game_link or not validate_url(game_link):
            self.logger.warning(f"⚠️ Link inválido para {game_teams}")
            self.failed_investigations.append({
                'game': game_data,
                'reason': 'Link inválido',
                'timestamp': datetime.now().isoformat()
            })
            return None
        
        with LogContext(self.logger, f"Investigação: {game_teams}"):
            try:
                # Navega para a página do jogo
                await self.page.goto(
                    game_link,
                    wait_until=PLAYWRIGHT_CONFIG['wait_until'],
                    timeout=TIMEOUTS['page_load']
                )
                
                # Aguarda carregamento do conteúdo
                await asyncio.sleep(INVESTIGATION_CONFIG['wait_after_load'])
                
                # Extrai dados detalhados
                detailed_data = await self._extract_detailed_data(game_data)
                
                if detailed_data:
                    self.investigated_games.append(detailed_data)
                    self.logger.info(f"✅ Investigação concluída: {game_teams}")
                    return detailed_data
                else:
                    self.logger.warning(f"⚠️ Nenhum dado detalhado encontrado: {game_teams}")
                    return None
            
            except Exception as e:
                self.logger.error(f"❌ Erro na investigação de {game_teams}: {e}")
                self.failed_investigations.append({
                    'game': game_data,
                    'reason': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                return None
    
    async def _extract_detailed_data(self, original_game_data):
        """Extrai dados detalhados da página do jogo"""
        detailed_data = {
            'original_data': original_game_data,
            'investigation_timestamp': datetime.now().isoformat(),
            'game_hash': generate_game_hash(original_game_data),
            'page_url': self.page.url,
            'page_title': await self.page.title(),
            'detailed_info': {}
        }
        
        # Extrai informações específicas baseadas nos seletores
        selectors_to_extract = {
            'game_details': SELECTORS.get('game_details', '.game-info'),
            'odds_table': SELECTORS.get('odds_table', '.odds-table'),
            'statistics': SELECTORS.get('statistics', '.stats'),
            'match_info': SELECTORS.get('match_info', '.match-details')
        }
        
        for info_type, selector in selectors_to_extract.items():
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    info_data = []
                    for element in elements:
                        text_content = await element.inner_text()
                        html_content = await element.inner_html()
                        info_data.append({
                            'text': text_content.strip(),
                            'html': html_content
                        })
                    detailed_data['detailed_info'][info_type] = info_data
                    self.logger.debug(f"📊 Extraído {info_type}: {len(info_data)} elementos")
            except Exception as e:
                self.logger.debug(f"⚠️ Erro ao extrair {info_type}: {e}")
        
        # Extrai metadados da página
        await self._extract_page_metadata(detailed_data)
        
        # Extrai informações de odds se disponível
        await self._extract_odds_info(detailed_data)
        
        return detailed_data
    
    async def _extract_page_metadata(self, detailed_data):
        """Extrai metadados da página"""
        try:
            # Meta tags
            meta_tags = await self.page.query_selector_all('meta')
            metadata = {}
            
            for meta in meta_tags:
                name = await meta.get_attribute('name')
                property_attr = await meta.get_attribute('property')
                content = await meta.get_attribute('content')
                
                if name and content:
                    metadata[name] = content
                elif property_attr and content:
                    metadata[property_attr] = content
            
            detailed_data['page_metadata'] = metadata
            
        except Exception as e:
            self.logger.debug(f"⚠️ Erro ao extrair metadados: {e}")
    
    async def _extract_odds_info(self, detailed_data):
        """Extrai informações de odds/apostas"""
        try:
            # Procura por tabelas de odds
            odds_selectors = [
                'table.odds',
                '.odds-table',
                '[class*="odd"]',
                '[class*="bet"]'
            ]
            
            odds_data = []
            
            for selector in odds_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and any(keyword in text.lower() for keyword in ['odd', 'bet', '1x2', 'over', 'under']):
                        odds_data.append({
                            'selector': selector,
                            'text': text.strip(),
                            'html': await element.inner_html()
                        })
            
            if odds_data:
                detailed_data['odds_info'] = odds_data
                self.logger.debug(f"🎯 Extraídas {len(odds_data)} informações de odds")
        
        except Exception as e:
            self.logger.debug(f"⚠️ Erro ao extrair odds: {e}")
    
    async def investigate_games_from_file(self, games_file_path):
        """Investiga jogos a partir de um arquivo de dados"""
        try:
            games_data = load_json_file(Path(games_file_path))
            games_list = games_data.get('games', [])
            
            if not games_list:
                self.logger.error("❌ Nenhum jogo encontrado no arquivo")
                return None
            
            # Limita número de jogos se configurado
            max_investigations = INVESTIGATION_CONFIG.get('max_games_per_run', len(games_list))
            if len(games_list) > max_investigations:
                games_list = games_list[:max_investigations]
                self.logger.info(f"🎯 Limitando investigação a {max_investigations} jogos")
            
            self.logger.info(f"🔍 Iniciando investigação de {len(games_list)} jogos")
            
            # Investiga cada jogo
            for i, game in enumerate(games_list):
                self.logger.info(f"🎮 Investigando jogo {i+1}/{len(games_list)}: {game.get('teams', 'N/A')}")
                
                await self.investigate_game(game)
                
                # Pausa entre investigações
                if i < len(games_list) - 1:
                    await asyncio.sleep(INVESTIGATION_CONFIG['delay_between_games'])
            
            return await self.save_investigation_results()
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao investigar jogos do arquivo: {e}")
            raise
    
    async def save_investigation_results(self):
        """Salva resultados da investigação"""
        timestamp = format_timestamp()
        filename = FILE_PATTERNS['investigation_results'].format(timestamp=timestamp)
        filepath = DATA_DIR / filename
        
        results = {
            'metadata': {
                'investigation_timestamp': datetime.now().isoformat(),
                'total_investigated': len(self.investigated_games),
                'total_failed': len(self.failed_investigations),
                'investigator_version': '2.0'
            },
            'summary': {
                'success_rate': len(self.investigated_games) / (len(self.investigated_games) + len(self.failed_investigations)) * 100 if (len(self.investigated_games) + len(self.failed_investigations)) > 0 else 0,
                'investigated_games': len(self.investigated_games),
                'failed_investigations': len(self.failed_investigations)
            },
            'investigated_games': self.investigated_games,
            'failed_investigations': self.failed_investigations
        }
        
        save_json_file(results, filepath)
        
        self.logger.info(f"💾 Resultados salvos: {filename}")
        return str(filepath)
    
    def print_investigation_summary(self):
        """Imprime resumo da investigação"""
        total_games = len(self.investigated_games) + len(self.failed_investigations)
        success_rate = (len(self.investigated_games) / total_games * 100) if total_games > 0 else 0
        
        print("\n" + "="*60)
        print("RESUMO DA INVESTIGAÇÃO DE JOGOS")
        print("="*60)
        
        print(f"🎯 Total de jogos processados: {total_games}")
        print(f"✅ Investigações bem-sucedidas: {len(self.investigated_games)}")
        print(f"❌ Investigações falharam: {len(self.failed_investigations)}")
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.failed_investigations:
            print(f"\n❌ Principais motivos de falha:")
            failure_reasons = {}
            for failure in self.failed_investigations:
                reason = failure['reason']
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            
            for reason, count in failure_reasons.items():
                print(f"   • {reason}: {count} jogos")
        
        if self.investigated_games:
            print(f"\n🎮 Exemplos de jogos investigados:")
            for i, game in enumerate(self.investigated_games[:3]):
                original = game['original_data']
                print(f"   {i+1}. {original['teams']} ({original['league']})")
                print(f"      🔗 URL: {game['page_url']}")
                print(f"      📊 Dados coletados: {len(game['detailed_info'])} seções")
    
    async def cleanup(self):
        """Limpa recursos do navegador"""
        if self.browser:
            await self.browser.close()
            self.logger.info("🧹 Recursos do navegador liberados")
    
    async def run_investigation(self, games_file_path):
        """Executa o processo completo de investigação"""
        self.logger.info("🔍 Iniciando processo de investigação")
        
        try:
            await self.setup_browser()
            results_file = await self.investigate_games_from_file(games_file_path)
            
            if results_file:
                self.print_investigation_summary()
                self.logger.info(f"✅ Investigação concluída: {results_file}")
                return results_file
            else:
                self.logger.error("❌ Nenhum resultado de investigação foi gerado")
                return None
        
        except Exception as e:
            self.logger.error(f"❌ Erro no processo de investigação: {e}")
            raise
        
        finally:
            await self.cleanup()

# Função de conveniência para uso direto
async def investigate_games(games_file_path):
    """Função de conveniência para investigar jogos"""
    investigator = GameInvestigator()
    return await investigator.run_investigation(games_file_path)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python investigator.py <caminho_arquivo_jogos>")
        sys.exit(1)
    
    games_file = sys.argv[1]
    asyncio.run(investigate_games(games_file))