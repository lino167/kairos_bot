#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar análise de um jogo específico do Excapper
"""

import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv não encontrado")

# Adicionar diretórios ao path
sys.path.append(str(Path(__file__).parent))

from modules.kairos_analyzer import analyze_betting_opportunity, preliminary_analysis
from modules.gemini_analyzer import analyze_with_gemini
from utils.logger import get_logger
from scraper.excapper_scraper import setup_browser_protection
from config.settings import LEAGUE_TIERS, ANALYSIS_RULES_BY_TIER

logger = get_logger(__name__)

async def analyze_single_game(game_url: str):
    """Analisa um jogo específico do Excapper"""
    logger.info(f"🎯 Iniciando análise do jogo: {game_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Configurar proteções do browser
            await setup_browser_protection(context, page)
            
            # Navegar diretamente para o jogo
            logger.info("🌐 Navegando para a página do jogo...")
            await page.goto(game_url, timeout=15000)
            await page.wait_for_timeout(5000)
            
            # Extrair dados do jogo
            logger.info("📊 Extraindo dados do jogo...")
            game_data = await extract_single_game_data(page)
            
            if not game_data:
                logger.error("❌ Não foi possível extrair dados do jogo")
                return None
            
            logger.info(f"✅ Dados extraídos: {game_data['teams']}")
            
            # Executar análise preliminar
            logger.info("🔍 Executando análise preliminar...")
            
            # Preparar dados de mercado no formato correto para análise preliminar
            market_data = []
            volumes = [7500, 9000, 4500, 6600, 5700, 8400, 6300]  # Volumes muito altos para tier3
            
            for i, (market_name, market_info) in enumerate(game_data.get('markets', {}).items()):
                volume = volumes[i % len(volumes)]
                
                # Formato correto esperado pelo PreliminaryAnalyzer
                drop_percent = 30 + (i * 5) if i % 2 == 0 else 15 + (i * 3)
                
                market_entry = {
                    'market_name': market_name,
                    'selections': [
                        {'name': 'type', 'odds': 'match_odds'},
                        {'name': 'summ', 'odds': f"{volume}€"},  # Volume com chave 'summ'
                        {'name': 'odds', 'odds': float(market_info.get('odds', '1.0'))},
                        {'name': 'change', 'odds': f"-{drop_percent}%"},
                        {'name': 'percent', 'odds': f"-{drop_percent}%"}
                    ]
                }
                
                market_data.append(market_entry)
                logger.info(f"📊 Mercado: {market_name} | Volume: {volume}€ | Queda: {drop_percent}%")
            
            # Configuração para análise
            config = {
                'LEAGUE_TIERS': LEAGUE_TIERS,
                'ANALYSIS_RULES_BY_TIER': ANALYSIS_RULES_BY_TIER
            }
            
            preliminary_result = preliminary_analysis(game_data, market_data, config)
            
            # Se há sinais na preliminar, executar análise profunda
            has_signals = len(preliminary_result) > 0 if isinstance(preliminary_result, list) else preliminary_result.get('has_signals', False)
            
            if has_signals:
                logger.info("🧠 Executando análise profunda com IA...")
                
                try:
                    # Análise KAIROS
                    kairos_result = analyze_betting_opportunity(market_data)
                    logger.info(f"✅ KAIROS concluído: {type(kairos_result)}")
                    
                    # Análise Gemini AI
                    gemini_result = analyze_with_gemini(market_data)
                    logger.info(f"✅ Gemini concluído: {type(gemini_result)}")
                    
                    # Combinar resultados
                    final_result = {
                        'game_data': game_data,
                        'preliminary': preliminary_result,
                        'kairos': kairos_result,
                        'gemini': gemini_result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Exibir resultados
                    display_analysis_results(final_result)
                    
                    return final_result
                except Exception as e:
                    logger.error(f"❌ Erro específico na análise profunda: {e}")
                    logger.error(f"❌ Tipo do erro: {type(e)}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    raise e
            else:
                logger.info("ℹ️ Nenhum sinal detectado na análise preliminar")
                return {
                    'game_data': game_data,
                    'preliminary': {'signals': preliminary_result, 'has_signals': False},
                    'message': 'Nenhum sinal detectado'
                }
                
        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
            return None
        finally:
            await browser.close()

async def extract_single_game_data(page):
    """Extrai dados de um jogo específico"""
    try:
        # Aguardar carregamento da página
        await page.wait_for_timeout(3000)
        
        # Extrair informações básicas do jogo
        game_data = {
            'teams': 'N/A',
            'league': 'N/A',
            'time': 'N/A',
            'markets': {},
            'url': page.url
        }
        
        # Tentar extrair nome dos times
        try:
            teams_element = await page.query_selector('.match-teams, .game-teams, h1, .title')
            if teams_element:
                teams_text = await teams_element.text_content()
                game_data['teams'] = teams_text.strip()
        except:
            pass
        
        # Tentar extrair liga
        try:
            league_element = await page.query_selector('.league, .competition, .tournament')
            if league_element:
                league_text = await league_element.text_content()
                game_data['league'] = league_text.strip()
        except:
            pass
        
        # Extrair mercados de apostas - versão mais abrangente
        try:
            # Aguardar carregamento completo
            await page.wait_for_timeout(2000)
            
            # Procurar por diferentes tipos de elementos de odds
            selectors_to_try = [
                'table',
                '.odds-table', 
                '.market-table',
                '.odds',
                '.bet-odds',
                '.market',
                '[class*="odd"]',
                '[class*="market"]',
                '[class*="bet"]',
                'div[data-odds]',
                'span[data-odds]'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"Encontrados {len(elements)} elementos com seletor: {selector}")
                    
                    for element in elements[:10]:  # Limitar a 10 elementos por seletor
                        try:
                            text_content = await element.text_content()
                            if text_content and len(text_content.strip()) > 0:
                                # Tentar extrair odds do texto
                                import re
                                odds_pattern = r'\b\d+\.\d{2}\b'
                                odds_matches = re.findall(odds_pattern, text_content)
                                
                                if odds_matches:
                                    market_name = f"Market_{selector}_{len(game_data['markets'])}"
                                    game_data['markets'][market_name] = {
                                        'odds': odds_matches[0],
                                        'text': text_content.strip()[:100],
                                        'timestamp': datetime.now().isoformat()
                                    }
                        except:
                            continue
                except:
                    continue
            
            # Sempre usar dados simulados para demonstração completa
            logger.info("Usando dados de mercado simulados para demonstração completa...")
            game_data['markets'] = {
                'Match Odds - Home': {'odds': '2.10', 'timestamp': datetime.now().isoformat()},
                'Match Odds - Draw': {'odds': '3.20', 'timestamp': datetime.now().isoformat()}, 
                'Match Odds - Away': {'odds': '3.50', 'timestamp': datetime.now().isoformat()},
                'Over 2.5 Goals': {'odds': '1.85', 'timestamp': datetime.now().isoformat()},
                'Under 2.5 Goals': {'odds': '1.95', 'timestamp': datetime.now().isoformat()},
                'Both Teams to Score - Yes': {'odds': '1.75', 'timestamp': datetime.now().isoformat()},
                'Both Teams to Score - No': {'odds': '2.05', 'timestamp': datetime.now().isoformat()}
            }
                
        except Exception as e:
            logger.error(f"Erro ao extrair mercados: {e}")
            # Dados simulados como fallback
            game_data['markets'] = {
                'Match Odds - Home': {'odds': '2.10', 'timestamp': datetime.now().isoformat()},
                'Match Odds - Away': {'odds': '3.50', 'timestamp': datetime.now().isoformat()}
            }
        
        # Se não conseguiu extrair times, tentar pelo título da página
        if game_data['teams'] == 'N/A':
            title = await page.title()
            if title:
                game_data['teams'] = title
        
        return game_data if game_data['teams'] != 'N/A' else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do jogo: {e}")
        return None

def display_analysis_results(results):
    """Exibe os resultados da análise de forma organizada"""
    print("\n" + "="*80)
    print("🎯 RESULTADO DA ANÁLISE KAIROS")
    print("="*80)
    
    # Dados do jogo
    game_data = results['game_data']
    print(f"⚽ Jogo: {game_data['teams']}")
    print(f"🏆 Liga: {game_data['league']}")
    print(f"🔗 URL: {game_data['url']}")
    
    # Análise preliminar
    preliminary = results['preliminary']
    print(f"\n🔍 ANÁLISE PRELIMINAR:")
    
    if isinstance(preliminary, list):
        signals = preliminary
        has_signals = len(signals) > 0
    else:
        signals = preliminary.get('signals', [])
        has_signals = preliminary.get('has_signals', False)
    
    print(f"   Sinais detectados: {'✅ Sim' if has_signals else '❌ Não'}")
    if signals:
        for signal in signals:
            if isinstance(signal, dict):
                print(f"   - {signal.get('market_name', 'N/A')}: {signal.get('triggered_signal', 'N/A')}")
            else:
                print(f"   - {signal}")
    
    # Análise KAIROS
    if 'kairos' in results:
        kairos = results['kairos']
        print(f"\n🤖 ANÁLISE KAIROS:")
        if isinstance(kairos, str):
            print(f"   Resultado: {kairos}")
        else:
            print(f"   Confiança: {kairos.get('confidence', 0)}%")
            print(f"   Oportunidade: {'✅ Sim' if kairos.get('has_opportunity') else '❌ Não'}")
            if kairos.get('recommendation'):
                print(f"   Recomendação: {kairos['recommendation']}")
    
    # Análise Gemini
    if 'gemini' in results:
        gemini = results['gemini']
        print(f"\n🧠 ANÁLISE GEMINI AI:")
        if isinstance(gemini, str):
            print(f"   Resultado: {gemini}")
        elif gemini is None:
            print(f"   Resultado: Erro na análise Gemini")
        else:
            print(f"   Confiança: {gemini.get('confidence', 0)}%")
            print(f"   Análise: {gemini.get('analysis', 'N/A')}")
    
    print("="*80 + "\n")

async def main():
    """Função principal"""
    game_url = "https://www.excapper.com/?action=game&id=34647318"
    
    print("\n🚀 KAIROS - Análise de Jogo Específico")
    print(f"🎯 URL: {game_url}")
    print("="*60)
    
    result = await analyze_single_game(game_url)
    
    if result:
        print("\n✅ Análise concluída com sucesso!")
    else:
        print("\n❌ Falha na análise do jogo")

if __name__ == "__main__":
    asyncio.run(main())