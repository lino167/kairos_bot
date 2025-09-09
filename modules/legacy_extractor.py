#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - EXTRAÇÃO COMPLETA DE DADOS DOS JOGOS
Extrai informações detalhadas de cada jogo incluindo links para páginas individuais
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin, unquote

class GameDataExtractor:
    def __init__(self):
        self.base_url = "https://www.excapper.com/"
        self.games_data = []
        self.browser = None
        self.page = None
    
    async def setup_browser(self):
        """Configura o navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        print("✅ Navegador configurado com sucesso")
    
    async def navigate_to_site(self):
        """Navega para o site principal"""
        print(f"🌐 Navegando para: {self.base_url}")
        await self.page.goto(self.base_url, wait_until='networkidle')
        
        # Aguarda o carregamento das tabelas
        await self.page.wait_for_selector('table', timeout=10000)
        print("✅ Página carregada com sucesso")
    
    async def extract_games_from_tables(self):
        """Extrai dados de todos os jogos das tabelas"""
        print("📊 Extraindo dados dos jogos...")
        
        # Encontra todas as linhas de jogos com classe 'a_link'
        game_rows = await self.page.query_selector_all('tr.a_link')
        print(f"🎯 Encontradas {len(game_rows)} linhas de jogos")
        
        for i, row in enumerate(game_rows):
            try:
                game_data = await self.extract_single_game_data(row, i)
                if game_data:
                    self.games_data.append(game_data)
                    print(f"✅ Jogo {i+1}/{len(game_rows)}: {game_data['teams']}")
            except Exception as e:
                print(f"❌ Erro ao extrair jogo {i+1}: {e}")
        
        print(f"📊 Total de jogos extraídos: {len(self.games_data)}")
    
    async def extract_single_game_data(self, row, index):
        """Extrai dados de um único jogo"""
        # Extrai atributos da linha
        game_id = await row.get_attribute('game_id')
        data_game_link = await row.get_attribute('data-game-link')
        
        # Extrai dados das células
        cells = await row.query_selector_all('td')
        
        if len(cells) < 5:
            return None
        
        # Extrai texto de cada célula
        date_time = await cells[0].inner_text()
        
        # Extrai informações do país (imagem)
        country_img = await cells[1].query_selector('img')
        country_info = {}
        if country_img:
            country_info = {
                'src': await country_img.get_attribute('src'),
                'alt': await country_img.get_attribute('alt'),
                'title': await country_img.get_attribute('title')
            }
        
        league = await cells[2].inner_text()
        teams = await cells[3].inner_text()
        money = await cells[4].inner_text()
        
        # Processa o link do jogo
        game_link = None
        if data_game_link:
            # Remove entidades HTML
            clean_link = data_game_link.replace('&amp;', '&')
            game_link = urljoin(self.base_url, clean_link.strip())
        
        # Extrai informações adicionais do HTML da linha
        row_html = await row.inner_html()
        
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
            'row_html': row_html,
            'extracted_at': datetime.now().isoformat()
        }
        
        # Tenta extrair informações adicionais dos times
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
        
        return game_data
    
    async def validate_game_links(self, sample_size=3):
        """Valida alguns links de jogos para verificar se funcionam"""
        print(f"🔍 Validando {sample_size} links de jogos...")
        
        valid_links = 0
        for i, game in enumerate(self.games_data[:sample_size]):
            if game.get('game_link'):
                try:
                    print(f"🌐 Testando link {i+1}: {game['game_link']}")
                    response = await self.page.goto(game['game_link'], timeout=10000)
                    if response.status == 200:
                        valid_links += 1
                        print(f"✅ Link válido: {game['teams']}")
                    else:
                        print(f"⚠️ Link retornou status {response.status}: {game['teams']}")
                except Exception as e:
                    print(f"❌ Erro ao acessar link: {e}")
        
        print(f"📊 Links válidos: {valid_links}/{sample_size}")
        return valid_links
    
    def generate_statistics(self):
        """Gera estatísticas dos dados extraídos"""
        if not self.games_data:
            return {}
        
        stats = {
            'total_games': len(self.games_data),
            'games_with_links': sum(1 for game in self.games_data if game.get('game_link')),
            'games_with_money': sum(1 for game in self.games_data if game.get('money_numeric', 0) > 0),
            'total_money': sum(game.get('money_numeric', 0) for game in self.games_data),
            'leagues': list(set(game['league'] for game in self.games_data if game.get('league'))),
            'countries': list(set(game['country'].get('alt', '') for game in self.games_data if game.get('country', {}).get('alt'))),
            'date_range': {
                'first': self.games_data[0]['date_time'] if self.games_data else None,
                'last': self.games_data[-1]['date_time'] if self.games_data else None
            }
        }
        
        return stats
    
    async def save_results(self):
        """Salva os resultados em arquivo JSON"""
        stats = self.generate_statistics()
        
        results = {
            'metadata': {
                'extraction_timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'total_games_extracted': len(self.games_data),
                'extractor_version': '1.0'
            },
            'statistics': stats,
            'games': self.games_data
        }
        
        filename = f"games_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dados salvos em: {filename}")
        return filename
    
    def print_summary(self):
        """Imprime resumo dos dados extraídos"""
        stats = self.generate_statistics()
        
        print("\n" + "="*60)
        print("RESUMO DA EXTRAÇÃO DE DADOS DOS JOGOS")
        print("="*60)
        
        print(f"🎯 Total de jogos: {stats['total_games']}")
        print(f"🔗 Jogos com links: {stats['games_with_links']}")
        print(f"💰 Jogos com valores: {stats['games_with_money']}")
        print(f"💵 Valor total: {stats['total_money']:,} €")
        print(f"🏆 Ligas únicas: {len(stats['leagues'])}")
        print(f"🌍 Países únicos: {len(stats['countries'])}")
        
        if stats['leagues']:
            print(f"\n📋 Principais ligas:")
            for league in stats['leagues'][:5]:
                print(f"   - {league}")
        
        if stats['countries']:
            print(f"\n🌍 Países encontrados:")
            for country in stats['countries'][:10]:
                if country:
                    print(f"   - {country}")
        
        # Mostra alguns exemplos de jogos
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
            print("🧹 Navegador fechado")
    
    async def run_extraction(self):
        """Executa o processo completo de extração"""
        print("="*70)
        print("KAIROS BOT - EXTRAÇÃO COMPLETA DE DADOS DOS JOGOS")
        print("="*70)
        
        try:
            await self.setup_browser()
            await self.navigate_to_site()
            await self.extract_games_from_tables()
            
            if self.games_data:
                await self.validate_game_links()
                filename = await self.save_results()
                self.print_summary()
                
                print("\n" + "="*70)
                print("EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
                print(f"📄 Arquivo gerado: {filename}")
                print("="*70)
            else:
                print("❌ Nenhum dado de jogo foi extraído")
        
        except Exception as e:
            print(f"❌ Erro durante a extração: {e}")
        
        finally:
            await self.cleanup()

if __name__ == "__main__":
    extractor = GameDataExtractor()
    asyncio.run(extractor.run_extraction())