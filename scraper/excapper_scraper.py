#!/usr/bin/env python3
"""
Módulo de Web Scraping para Excapper

Este módulo é responsável por extrair dados de partidas de futebol ao vivo
do site Excapper (https://www.excapper.com/), identificando oportunidades
de apostas baseadas em mudanças de odds.

Autor: Kairos Bot
Data: 2025
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time
from datetime import datetime
import sys
import os
import random
from typing import List, Dict, Optional

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.kairos_analyzer import analyze_betting_opportunity
from modules.gemini_analyzer import analyze_with_gemini

# Configurações de rate limiting para proteção
RATE_LIMIT_CONFIG = {
    'min_delay': 2,  # Mínimo 2 segundos entre requisições
    'max_delay': 5,  # Máximo 5 segundos entre requisições
    'page_load_timeout': 10000,  # 10 segundos timeout para carregamento
    'max_games_per_session': 50,  # Processar TODOS os jogos encontrados
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
}

def check_ai_opportunity(analysis_text: str) -> tuple[bool, dict]:
    """
    Verifica se a análise da IA identificou uma oportunidade real e extrai detalhes.
    
    Args:
        analysis_text: Texto da análise KAIROS
        
    Returns:
        tuple: (bool: há oportunidade, dict: detalhes da oportunidade)
    """
    if not analysis_text:
        return False, {}
    
    import re
    
    # Indicadores de oportunidade na análise
    opportunity_indicators = [
        'oportunidade identificada',
        'valor encontrado',
        'discrepância detectada',
        'arbitragem possível',
        'confiança: alta',
        'recomendação: apostar',
        'sinal positivo',
        'mercado favorável',
        'oportunidade encontrada: sim'
    ]
    
    # Indicadores de baixa confiança
    low_confidence_indicators = [
        'confiança: baixa',
        'dados insuficientes',
        'sem oportunidade clara',
        'mercado equilibrado',
        'aguardar mais dados',
        'oportunidade encontrada: não'
    ]
    
    analysis_lower = analysis_text.lower()
    
    # Verificar indicadores negativos primeiro
    for indicator in low_confidence_indicators:
        if indicator in analysis_lower:
            return False, {}
    
    # Extrair detalhes da oportunidade
    opportunity_details = {}
    
    # Extrair mercado sugerido
    market_match = re.search(r'mercado sugerido[:\s]*([^\n]+)', analysis_lower)
    if market_match:
        opportunity_details['suggested_market'] = market_match.group(1).strip()
    
    # Extrair seleção
    selection_match = re.search(r'seleção[:\s]*([^\n]+)', analysis_lower)
    if selection_match:
        opportunity_details['selection'] = selection_match.group(1).strip()
    
    # Extrair justificativa
    justification_match = re.search(r'justificativa[^:]*[:\s]*([^\n]+(?:\n[^\n]*)*?)(?=\n\d+\.|$)', analysis_text, re.IGNORECASE | re.MULTILINE)
    if justification_match:
        opportunity_details['justification'] = justification_match.group(1).strip()
    
    # Verificar indicadores positivos
    has_opportunity = False
    for indicator in opportunity_indicators:
        if indicator in analysis_lower:
            has_opportunity = True
            break
    
    # Verificar confiança numérica (acima de 60%)
    if not has_opportunity:
        confidence_match = re.search(r'confiança[:\s]*([0-9]+(?:\.[0-9]+)?)%', analysis_lower)
        if confidence_match:
            confidence = float(confidence_match.group(1))
            has_opportunity = confidence >= 60.0
    
    return has_opportunity, opportunity_details if has_opportunity else {}

def extract_confidence_from_analysis(analysis_text: str) -> float:
    """
    Extrai o nível de confiança da análise KAIROS.
    
    Args:
        analysis_text: Texto da análise KAIROS
        
    Returns:
        float: Nível de confiança (0-100)
    """
    if not analysis_text:
        return 0.0
    
    import re
    
    # Procurar por padrões de confiança
    confidence_patterns = [
        r'confiança[:\s]*([0-9]+(?:\.[0-9]+)?)%',
        r'confidence[:\s]*([0-9]+(?:\.[0-9]+)?)%',
        r'([0-9]+(?:\.[0-9]+)?)%\s*confiança'
    ]
    
    for pattern in confidence_patterns:
        match = re.search(pattern, analysis_text.lower())
        if match:
            return float(match.group(1))
    
    # Se não encontrar padrão numérico, usar indicadores textuais
    if 'alta' in analysis_text.lower():
        return 80.0
    elif 'média' in analysis_text.lower():
        return 50.0
    elif 'baixa' in analysis_text.lower():
        return 20.0
    
    return 0.0

async def safe_delay():
    """
    Implementa delay aleatório para evitar detecção como bot.
    """
    delay = random.uniform(RATE_LIMIT_CONFIG['min_delay'], RATE_LIMIT_CONFIG['max_delay'])
    print(f"⏱️ Aguardando {delay:.1f}s para próxima ação...")
    await asyncio.sleep(delay)

async def setup_browser_protection(context, page):
    """
    Configura proteções no browser para evitar detecção.
    
    Args:
        context: Contexto do browser
        page: Página do Playwright
    """
    # User agent aleatório
    user_agent = random.choice(RATE_LIMIT_CONFIG['user_agents'])
    
    # Configurar viewport
    await page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Adicionar headers para parecer mais humano
    await page.set_extra_http_headers({
        'User-Agent': user_agent,
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    print(f"🛡️ Proteções configuradas - User Agent: {user_agent[:50]}...")

async def extract_live_game_details(page) -> dict:
    """
    Extrai detalhes específicos do jogo ao vivo (placar, status, etc.).
    
    Args:
        page: Página do Playwright
        
    Returns:
        dict: Detalhes do jogo
    """
    game_details = {}
    
    try:
        # Tentar extrair placar atual
        score_selectors = [
            '.score',
            '.live-score', 
            '.current-score',
            '[class*="score"]',
            '.match-score'
        ]
        
        for selector in score_selectors:
            try:
                score_element = await page.query_selector(selector)
                if score_element:
                    score_text = await score_element.text_content()
                    if score_text and score_text.strip():
                        game_details['current_score'] = score_text.strip()
                        break
            except:
                continue
        
        # Tentar extrair status do jogo
        status_selectors = [
            '.match-status',
            '.game-status',
            '.live-status',
            '[class*="status"]',
            '.time'
        ]
        
        for selector in status_selectors:
            try:
                status_element = await page.query_selector(selector)
                if status_element:
                    status_text = await status_element.text_content()
                    if status_text and status_text.strip():
                        game_details['match_status'] = status_text.strip()
                        break
            except:
                continue
        
        # Extrair título da página para mais contexto
        try:
            title = await page.title()
            game_details['page_title'] = title
        except:
            pass
            
    except Exception as e:
        print(f"⚠️ Erro ao extrair detalhes do jogo: {e}")
    
    return game_details

def find_betfair_link_for_market(processed_markets: List[Dict], market_name: str) -> str:
    """
    Encontra o link Betfair para um mercado específico.
    
    Args:
        processed_markets: Lista de mercados processados
        market_name: Nome do mercado procurado
        
    Returns:
        str: Link Betfair ou string vazia
    """
    for market in processed_markets:
        if market.get('market_name', '').lower() == market_name.lower():
            return market.get('betfair_link', '')
    return ''

def create_detailed_opportunity_report(game: dict, opportunity_details: dict, processed_markets: List[Dict]) -> str:
    """
    Cria um relatório detalhado da oportunidade encontrada.
    
    Args:
        game: Dados do jogo
        opportunity_details: Detalhes da oportunidade
        processed_markets: Mercados processados
        
    Returns:
        str: Relatório formatado
    """
    report = []
    report.append("\n" + "="*80)
    report.append("🎯 OPORTUNIDADE IDENTIFICADA PELA IA KAIROS!")
    report.append("="*80)
    
    # Dados básicos do jogo
    report.append(f"\n📊 DADOS DO JOGO:")
    report.append(f"   🏆 Liga: {game.get('league', 'N/A')}")
    report.append(f"   ⚽ Times: {game.get('teams', 'N/A')}")
    report.append(f"   📅 Data/Hora: {game.get('datetime', 'N/A')}")
    report.append(f"   💰 Volume: {game.get('money', 'N/A')}")
    
    # Placar atual se disponível
    if game.get('current_score'):
        report.append(f"   ⚽ Placar Atual: {game.get('current_score')}")
    
    if game.get('match_status'):
        report.append(f"   ⏱️ Status: {game.get('match_status')}")
    
    # Detalhes da oportunidade
    report.append(f"\n🎯 OPORTUNIDADE DETECTADA:")
    if opportunity_details.get('suggested_market'):
        report.append(f"   📈 Mercado: {opportunity_details['suggested_market']}")
    
    if opportunity_details.get('selection'):
        report.append(f"   ✅ Seleção: {opportunity_details['selection']}")
    
    # Link Betfair específico
    if opportunity_details.get('suggested_market'):
        betfair_link = find_betfair_link_for_market(processed_markets, opportunity_details['suggested_market'])
        if betfair_link:
            report.append(f"   🔗 Link Betfair: {betfair_link}")
    
    report.append(f"   🎯 Confiança: {game.get('ai_confidence', 0):.1f}%")
    
    # Justificativa detalhada
    if opportunity_details.get('justification'):
        report.append(f"\n💡 EXPLICAÇÃO DA OPORTUNIDADE:")
        justification_lines = opportunity_details['justification'].split('\n')
        for line in justification_lines:
            if line.strip():
                report.append(f"   {line.strip()}")
    
    # Análise dos mercados relevantes
    if opportunity_details.get('suggested_market'):
        relevant_market = None
        for market in processed_markets:
            if market.get('market_name', '').lower() == opportunity_details['suggested_market'].lower():
                relevant_market = market
                break
        
        if relevant_market:
            report.append(f"\n📊 DADOS DO MERCADO '{relevant_market['market_name']}':")
            selections = relevant_market.get('selections', [])
            for i, selection in enumerate(selections[:10]):  # Mostrar até 10 seleções
                name = selection.get('name', 'N/A')
                odds = selection.get('odds', 'N/A')
                report.append(f"   {i+1}. {name}: {odds}")
            
            if len(selections) > 10:
                report.append(f"   ... e mais {len(selections) - 10} seleções")
    
    report.append(f"\n🌐 Link do Jogo: {game.get('game_link', 'N/A')}")
    report.append("="*80)
    
    return "\n".join(report)

async def process_multiple_games_safely(live_games_data: List[Dict], page) -> List[Dict]:
    """
    Processa múltiplos jogos de forma segura com rate limiting.
    
    Args:
        live_games_data: Lista de jogos para processar
        page: Página do Playwright
        
    Returns:
        List[Dict]: Jogos processados com análises
    """
    processed_games = []
    max_games = min(len(live_games_data), RATE_LIMIT_CONFIG['max_games_per_session'])
    
    print(f"\n🎯 Processando {max_games} jogos de forma segura...")
    
    for i, game in enumerate(live_games_data[:max_games]):
        print(f"\n📊 Processando jogo {i+1}/{max_games}: {game.get('teams', 'N/A')}")
        
        game_link = game.get('game_link')
        if not game_link:
            print("⚠️ Link do jogo não encontrado, pulando...")
            game['has_prediction'] = False
            game['ai_confidence'] = 0
            processed_games.append(game)
            continue
        
        try:
            # Delay de segurança antes de navegar
            if i > 0:  # Não fazer delay no primeiro jogo
                await safe_delay()
            
            print(f"🌐 Navegando para: {game_link}")
            await page.goto(game_link, timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
            await page.wait_for_timeout(3000)  # Aguarda carregamento
            
            # Extrair detalhes específicos do jogo
            game_details = await extract_live_game_details(page)
            game.update(game_details)
            
            # Processar mercados do jogo
            processed_markets = await process_game_page_tables(page)
            
            if processed_markets:
                print(f"✅ {len(processed_markets)} mercados processados")
                
                # Análise KAIROS
                print(f"🤖 Executando análise KAIROS...")
                kairos_analysis = analyze_betting_opportunity(processed_markets)
                
                # Verificar oportunidade com detalhes
                has_opportunity, opportunity_details = check_ai_opportunity(kairos_analysis)
                game['has_prediction'] = has_opportunity
                game['ai_confidence'] = extract_confidence_from_analysis(kairos_analysis)
                game['opportunity_details'] = opportunity_details
                
                # Análise Gemini para TODOS os jogos (análise de movimentação de mercado)
                try:
                    game_context = {
                        'teams': game.get('teams', 'N/A'),
                        'league': game.get('league', 'N/A'),
                        'datetime': game.get('datetime', 'N/A'),
                        'status': 'live',
                        'current_score': game.get('current_score', 'N/A'),
                        'match_status': game.get('match_status', 'N/A')
                    }
                    
                    print(f"🧠 Executando análise Gemini (movimentação de mercado)...")
                    gemini_analysis = analyze_with_gemini(processed_markets, game_context)
                    game['gemini_analysis'] = gemini_analysis
                    print(f"✅ Análise Gemini concluída")
                    
                    # Verificar se Gemini identificou oportunidade adicional
                    if gemini_analysis and "oportunidade" in gemini_analysis.lower():
                        print(f"🎯 Gemini identificou possível oportunidade adicional!")
                        
                except Exception as e:
                    print(f"⚠️ Erro na análise Gemini: {e}")
                    game['gemini_analysis'] = None
                
                if has_opportunity:
                    print(f"✅ OPORTUNIDADE IDENTIFICADA PELA KAIROS! Confiança: {game['ai_confidence']:.1f}%")
                    
                    # Criar relatório detalhado
                    detailed_report = create_detailed_opportunity_report(game, opportunity_details, processed_markets)
                    print(detailed_report)
                    game['detailed_report'] = detailed_report
                else:
                    print(f"⚠️ KAIROS: Nenhuma oportunidade clara (Confiança: {game['ai_confidence']:.1f}%)")
                
                game['kairos_analysis'] = kairos_analysis
                game['processed_markets'] = processed_markets
                
            else:
                print("❌ Nenhum mercado processado")
                game['has_prediction'] = False
                game['ai_confidence'] = 0
                game['kairos_analysis'] = None
                game['gemini_analysis'] = None
                
        except Exception as e:
            print(f"❌ Erro ao processar jogo {i+1}: {e}")
            game['has_prediction'] = False
            game['ai_confidence'] = 0
            game['error'] = str(e)
        
        processed_games.append(game)
        
        # Status do progresso
        opportunities_found = sum(1 for g in processed_games if g.get('has_prediction', False))
        print(f"📈 Progresso: {i+1}/{max_games} jogos | {opportunities_found} oportunidades encontradas")
    
    return processed_games

async def process_game_page_tables(page):
    """
    Processa todas as abas de mercados da página de um jogo, extraindo dados de cada tabela.
    
    Args:
        page: Objeto page do Playwright
        
    Returns:
        list: Lista de mercados processados com suas seleções e odds
    """
    print("[KAIROS] Extraindo dados de todas as abas de mercados...")
    
    processed_markets = []
    
    try:
        # Localizar todas as abas do menu
        tab_links = await page.locator('.smenu a.tab').all()
        print(f"[KAIROS] {len(tab_links)} abas de mercados encontradas.")
        
        for i, tab_link in enumerate(tab_links):
            try:
                # Obter o nome do mercado do texto da aba
                market_name = await tab_link.text_content()
                market_name = market_name.strip() if market_name else f"Mercado {i+1}"
                
                print(f"[KAIROS] Processando aba: {market_name}")
                
                # Clicar na aba para ativá-la
                await tab_link.click()
                await page.wait_for_timeout(1000)  # Aguardar carregamento da aba
                
                # Obter o data-tab para localizar o conteúdo correspondente
                data_tab = await tab_link.get_attribute('data-tab')
                
                if data_tab:
                    # Localizar a tabela dentro do conteúdo da aba
                    tab_content = page.locator(f'#{data_tab}')
                    tables_in_tab = await tab_content.locator('table').all()
                    
                    if not tables_in_tab:
                        print(f"⚠️ Nenhuma tabela encontrada na aba {market_name}")
                        continue
                    
                    # Processar a primeira tabela da aba
                    table_locator = tables_in_tab[0]
                    
                    # Extrair todas as linhas da tabela
                    all_rows = await table_locator.locator('tr').all()
                    
                    if len(all_rows) < 2:  # Precisa de pelo menos cabeçalho + 1 linha de dados
                        print(f"⚠️ Tabela na aba {market_name} não tem dados suficientes")
                        continue
                        
                    # Separar cabeçalho e linhas de dados
                    header_row = all_rows[0]
                    data_rows = all_rows[1:]
                    
                    # Extrair cabeçalhos
                    header_cells = await header_row.locator('xpath=./th | ./td').all()
                    headers = []
                    for cell in header_cells:
                        cell_text = await cell.text_content()
                        headers.append(cell_text.strip() if cell_text else "")
                    
                    # Processar linhas de dados
                    selections = []
                    
                    for data_row in data_rows:
                        data_cells = await data_row.locator('xpath=./th | ./td').all()
                        row_data = []
                        
                        for cell in data_cells:
                             cell_text = await cell.text_content()
                             row_data.append(cell_text.strip() if cell_text else "")
                        
                        # Criar seleções baseadas nos cabeçalhos e dados
                        for j, (header, data) in enumerate(zip(headers, row_data)):
                            if header and data:  # Só processar se ambos existirem
                                # Tentar converter para float (odds)
                                odds_value = data
                                try:
                                    odds_value = float(data.replace(',', '.'))  # Lidar com vírgulas decimais
                                except (ValueError, AttributeError):
                                    # Manter como string se não for numérico
                                    pass
                                
                                selection = {
                                    "name": header,
                                    "odds": odds_value
                                }
                                selections.append(selection)
                        
                        # Para tabelas com múltiplas linhas, só processar a primeira linha de dados
                        break
                    
                    # Extrair links da Betfair do elemento .smenu2
                    betfair_links = {}
                    try:
                        smenu2_elements = await tab_content.locator('.smenu2').all()
                        if smenu2_elements:
                            smenu2_element = smenu2_elements[0]
                            # Procurar por links da Betfair
                            betfair_link_elements = await smenu2_element.locator('a[href*="betfair.com"]').all()
                            if betfair_link_elements:
                                betfair_link_element = betfair_link_elements[0]
                                betfair_url = await betfair_link_element.get_attribute('href')
                                betfair_text = await betfair_link_element.text_content()
                                if betfair_url:
                                    betfair_links['betfair_url'] = betfair_url.strip()
                                    betfair_links['betfair_id'] = betfair_text.strip() if betfair_text else ""
                                    print(f"🔗 Link Betfair encontrado: {betfair_url}")
                            
                            # Procurar por outros links úteis (LiveCapper, etc.)
                            other_links = await smenu2_element.locator('a[href]').all()
                            for link in other_links:
                                href = await link.get_attribute('href')
                                text = await link.text_content()
                                if href and 'ecapper.ru' in href:
                                    betfair_links['livecapper_url'] = href.strip()
                                elif href and 'graph' in (text or '').lower():
                                    # Links de gráficos podem ser úteis futuramente
                                    pass
                    except Exception as e:
                        print(f"⚠️ Erro ao extrair links da aba {market_name}: {e}")
                    
                    # Montar objeto final do mercado
                    if selections:  # Só adicionar se tiver seleções válidas
                        market = {
                            "market_name": market_name,
                            "selections": selections,
                            "links": betfair_links if betfair_links else {}
                        }
                        processed_markets.append(market)
                        print(f"✅ Mercado '{market_name}' processado com {len(selections)} seleções")
                        if betfair_links.get('betfair_url'):
                            print(f"   📊 Betfair: {betfair_links['betfair_url']}")
                    else:
                        print(f"⚠️ Nenhuma seleção válida encontrada para {market_name}")
                        
            except Exception as e:
                print(f"⚠️ Erro ao processar aba {market_name}: {e}")
                continue
    
    except Exception as e:
        print(f"❌ Erro geral ao processar abas: {e}")
    
    return processed_markets


async def get_excapper_live_games() -> list:
    """
    Extrai dados de jogos ao vivo do site Excapper.
    
    Returns:
        list: Lista de jogos/oportunidades encontradas
    """
    async with async_playwright() as p:
        # Iniciar navegador em modo não-headless para visualizar a automação
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navegar para a página inicial do Excapper
            await page.goto('https://www.excapper.com/')
            print("📍 Navegando para Excapper...")
            
            # TODO: Encontrar o seletor do botão 'Live' e clicar nele
            print("🔍 Procurando pelo botão Live...")
            live_button_selector = 'a[href*="live"]'  # Seletor encontrado
            
            try:
                await page.wait_for_selector(live_button_selector, timeout=10000)
                await page.click(live_button_selector)  # Clique no botão Live
                print("✅ Botão Live clicado com sucesso!")
                
            except Exception as e:
                print(f"❌ Erro ao clicar no botão Live: {e}")
                return []
            
            # Etapa 2: Aguardar e localizar a tabela de jogos ao vivo
            print("[KAIROS] Aguardando a tabela de jogos ao vivo carregar...")
            await page.wait_for_timeout(3000)  # Aguarda 3 segundos para carregamento
            games_table = page.locator('table').first  # Primeira tabela (principal)
            print("[KAIROS] Tabela encontrada!")
            
            # TODO: Iterar sobre as linhas (os jogos) da variável 'games_table'
            # TODO: Para cada jogo, extrair os dados relevantes
            # TODO: Definir a lógica para identificar um 'sinal de oportunidade'
            
            # Código temporário para manter funcionalidade existente
            # Verificar se existem tabelas
            tables = await page.query_selector_all('table')
            print(f"✅ Encontradas {len(tables)} tabelas na página!")
            
            if len(tables) < 2:
                print("❌ Tabela principal de jogos não encontrada!")
                return []
            
            # Usar a segunda tabela (índice 1) que contém os jogos
            main_table = tables[1]
            rows = await main_table.query_selector_all('tr')
            print(f"📊 Encontradas {len(rows)} linhas na tabela de jogos")
            
            games_data = []
            
            try:
                # Pular a primeira linha (cabeçalho) e processar as demais
                for i, row in enumerate(rows[1:], 1):
                    try:
                        cells = await row.query_selector_all('td')
                        
                        # Verificar se a linha tem células suficientes (5 colunas: Data, Country, League, Teams, All money)
                        if len(cells) >= 5:
                            # Extrair dados das células baseado na estrutura descoberta
                            date_time = await cells[0].text_content()  # Data
                            country = await cells[1].text_content()    # Country
                            league = await cells[2].text_content()     # League
                            teams = await cells[3].text_content()      # Teams
                            money = await cells[4].text_content()      # All money
                            
                            # Extrair o link da página do jogo do atributo data-game-link da linha
                            game_link = None
                            try:
                                # O link está no atributo data-game-link da linha <tr>
                                game_link = await row.get_attribute('data-game-link')
                                if game_link:
                                    print(f"🔗 Link encontrado para linha {i}: {game_link}")
                            except Exception as e:
                                print(f"⚠️ Erro ao extrair link da linha {i}: {e}")
                            
                            # Limpar os textos
                            date_time = date_time.strip() if date_time else ""
                            country = country.strip() if country else ""
                            league = league.strip() if league else ""
                            teams = teams.strip() if teams else ""
                            money = money.strip() if money else ""
                            
                            # Verificar se os dados são válidos
                            if date_time and teams and league:
                                game_info = {
                                    'row_number': i,
                                    'datetime': date_time,
                                    'country': country,
                                    'league': league,
                                    'teams': teams,
                                    'money': money,
                                    'game_link': game_link,
                                    'opportunity_signal': None
                                }
                                
                                # Lógica para identificar sinais de oportunidade baseado no valor
                                if money and money != "":
                                    try:
                                        # Tentar extrair valor numérico
                                        value_str = money.replace('€', '').replace(',', '').replace('$', '').strip()
                                        if value_str.isdigit():
                                            value_num = int(value_str)
                                            
                                            # Definir critérios de oportunidade
                                            if value_num > 5000:  # Valores altos podem indicar oportunidades
                                                game_info['opportunity_signal'] = f'Alto volume: {money}'
                                            elif value_num > 1000:
                                                game_info['opportunity_signal'] = f'Volume médio: {money}'
                                    except:
                                        pass
                                
                                games_data.append(game_info)
                                
                                # Limitar a 20 jogos para não sobrecarregar
                                if len(games_data) >= 20:
                                    break
                    
                    except Exception as e:
                        print(f"⚠️ Erro ao processar linha {i}: {e}")
                        continue
                
                print(f"✅ Extraídos {len(games_data)} jogos com dados válidos")
                
                # Armazenar a lista de jogos ao vivo
                live_games_data = games_data
                
                # Verificar se a lista não está vazia e navegar para o primeiro jogo
                if live_games_data:
                    print(f"[KAIROS] {len(live_games_data)} jogos ao vivo encontrados. Testando o primeiro...")
                    first_game = live_games_data[0]
                    game_link = first_game.get('game_link')
                    
                    if game_link:
                        print(f"[KAIROS] Navegando para a página do primeiro jogo: {game_link}")
                        await page.goto(game_link)
                        await page.wait_for_timeout(5000)  # Espera 5s para a página carregar completamente
                        
                        # TODO: Encontrar os seletores para os dados detalhados na página do jogo
                        # TODO: Extrair placar, minuto do jogo e outras informações relevantes
                        print("[KAIROS] Página do jogo carregada. Pronto para a próxima etapa de extração.")
                        
                        # Processar tabelas da página de forma estruturada
                        processed_markets = await process_game_page_tables(page)
                        
                        print(f"\n[KAIROS] === MERCADOS PROCESSADOS ===")
                        for i, market in enumerate(processed_markets):
                            print(f"\n--- Mercado {i+1}: {market['market_name']} ---")
                            for selection in market['selections']:
                                print(f"  {selection['name']}: {selection['odds']}")
                            print("------------------")
                        
                        print(f"\n[KAIROS] Total de {len(processed_markets)} mercados processados com sucesso!")
                        
                                # 🧠 ANÁLISE KAIROS - Processar dados com IA
                        print(f"\n🤖 Iniciando análise KAIROS dos mercados...")
                        try:
                            # Análise KAIROS local
                            kairos_analysis = analyze_betting_opportunity(processed_markets)
                            print(f"\n{kairos_analysis}")
                            
                            # Verificar se há oportunidade identificada pela IA
                            has_opportunity = check_ai_opportunity(kairos_analysis)
                            
                            if has_opportunity:
                                print(f"\n✅ Oportunidade identificada pela IA! Executando análise avançada...")
                                
                                # Análise avançada com Gemini AI apenas se há oportunidade
                                print(f"\n🧠 Iniciando análise avançada com Gemini AI...")
                                game_context = {
                                    'teams': first_game.get('teams', 'N/A'),
                                    'league': first_game.get('league', 'N/A'),
                                    'datetime': first_game.get('datetime', 'N/A'),
                                    'status': 'live' if 'live' in str(processed_markets).lower() else 'prematch'
                                }
                                
                                gemini_analysis = analyze_with_gemini(processed_markets, game_context)
                                print(f"\n{gemini_analysis}")
                                
                                # Marcar jogo como tendo prognóstico
                                first_game['has_prediction'] = True
                                first_game['ai_confidence'] = extract_confidence_from_analysis(kairos_analysis)
                            else:
                                print(f"\n⚠️ Nenhuma oportunidade clara identificada pela IA. Pulando análise avançada.")
                                first_game['has_prediction'] = False
                                first_game['ai_confidence'] = 0
                            
                        except Exception as e:
                            print(f"❌ Erro na análise KAIROS: {e}")
                            first_game['has_prediction'] = False
                            first_game['ai_confidence'] = 0
                    else:
                        print("⚠️ Link do primeiro jogo não encontrado ou inválido")
                else:
                    print("❌ Nenhum jogo ao vivo encontrado")
                
                # Filtrar apenas jogos com sinais de oportunidade (opcional)
                opportunities = [game for game in live_games_data if game.get('opportunity_signal')]
                
                if opportunities:
                    print(f"🎯 Encontradas {len(opportunities)} oportunidades!")
                    return opportunities
                else:
                    print("📊 Retornando todos os jogos encontrados")
                    return live_games_data[:10]  # Limitar a 10 para teste
                
            except Exception as e:
                print(f"❌ Erro ao extrair dados da tabela: {e}")
                return []
            
        except Exception as e:
            print(f"Erro durante a extração: {e}")
            return []
        
        finally:
            await browser.close()


async def extract_live_games_data(page):
    """
    Extrai dados dos jogos ao vivo da página principal.
    
    Args:
        page: Página do Playwright
        
    Returns:
        List[Dict]: Lista de jogos encontrados
    """
    games_data = []
    
    try:
        # Aguardar carregamento da tabela
        await page.wait_for_timeout(3000)
        tables = await page.query_selector_all('table')
        
        if len(tables) < 2:
            print("❌ Tabela principal de jogos não encontrada!")
            return []
        
        # Usar a segunda tabela (índice 1) que contém os jogos
        main_table = tables[1]
        rows = await main_table.query_selector_all('tr')
        print(f"📊 Encontradas {len(rows)} linhas na tabela de jogos")
        
        # Pular a primeira linha (cabeçalho) e processar as demais
        for i, row in enumerate(rows[1:], 1):
            try:
                cells = await row.query_selector_all('td')
                
                # Verificar se a linha tem células suficientes
                if len(cells) >= 5:
                    # Extrair dados das células
                    date_time = await cells[0].text_content()
                    country = await cells[1].text_content()
                    league = await cells[2].text_content()
                    teams = await cells[3].text_content()
                    money = await cells[4].text_content()
                    
                    # Extrair o link da página do jogo
                    game_link = await row.get_attribute('data-game-link')
                    
                    # Limpar os textos
                    date_time = date_time.strip() if date_time else ""
                    country = country.strip() if country else ""
                    league = league.strip() if league else ""
                    teams = teams.strip() if teams else ""
                    money = money.strip() if money else ""
                    
                    # Verificar se os dados são válidos
                    if date_time and teams and league:
                        game_info = {
                            'row_number': i,
                            'datetime': date_time,
                            'country': country,
                            'league': league,
                            'teams': teams,
                            'money': money,
                            'game_link': game_link,
                            'opportunity_signal': None
                        }
                        
                        games_data.append(game_info)
                        
                        # Limitar a 20 jogos para não sobrecarregar
                        if len(games_data) >= 20:
                            break
            
            except Exception as e:
                print(f"⚠️ Erro ao processar linha {i}: {e}")
                continue
        
        print(f"✅ Extraídos {len(games_data)} jogos com dados válidos")
        return games_data
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados da tabela: {e}")
        return []

async def run_excapper_analysis():
    """Função principal para executar análise do Excapper."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Configurar proteções do browser
            await setup_browser_protection(context, page)
            
            # Navegar para a página principal
            print("🌐 Navegando para Excapper...")
            await page.goto("https://www.excapper.com/", timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
            await page.wait_for_timeout(3000)
            
            # Clicar no botão Live - tentar diferentes seletores
            print("🔴 Procurando botão Live...")
            
            # Aguardar carregamento completo
            await page.wait_for_timeout(5000)
            
            # Tentar diferentes seletores para o botão Live
            live_selectors = [
                'a[href="/live"]',
                'a[href="live"]', 
                'a:has-text("Live")',
                'a:has-text("LIVE")',
                '.nav-link:has-text("Live")',
                'button:has-text("Live")',
                '[data-bs-target="#live"]'
            ]
            
            live_clicked = False
            for selector in live_selectors:
                try:
                    live_button = await page.query_selector(selector)
                    if live_button:
                        print(f"✅ Botão Live encontrado com seletor: {selector}")
                        await live_button.click()
                        live_clicked = True
                        break
                except Exception as e:
                    continue
            
            if not live_clicked:
                print("⚠️ Botão Live não encontrado, tentando navegar diretamente...")
                await page.goto("https://www.excapper.com/live", timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
            
            # Aguardar carregamento da página Live
            await page.wait_for_timeout(5000)
            
            # Extrair dados dos jogos
            print("📊 Extraindo dados dos jogos ao vivo...")
            games_data = await extract_live_games_data(page)
            
            if games_data:
                print(f"\n📋 Encontrados {len(games_data)} jogos ao vivo")
                
                # Processar cada jogo individualmente
                processed_games = []
                
                for i, game in enumerate(games_data[:5], 1):  # Limitar a 5 jogos
                    print(f"\n🎯 Processando jogo {i}/{min(5, len(games_data))}: {game['teams']}")
                    
                    # Verificar se há link para página individual
                    if game.get('game_link'):
                        print(f"🔗 Acessando página individual do jogo...")
                        
                        try:
                            # Navegar para página do jogo
                            await page.goto(game['game_link'], timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
                            await page.wait_for_timeout(3000)
                            
                            # Extrair detalhes adicionais
                            game_details = await extract_live_game_details(page)
                            game.update(game_details)
                            
                            # Processar mercados do jogo
                            processed_markets = await process_game_page_tables(page)
                            
                            if processed_markets:
                                print(f"✅ {len(processed_markets)} mercados processados")
                                
                                # Análise KAIROS
                                print(f"🤖 Executando análise KAIROS...")
                                kairos_analysis = analyze_betting_opportunity(processed_markets)
                                
                                # Verificar oportunidade com detalhes
                                has_opportunity, opportunity_details = check_ai_opportunity(kairos_analysis)
                                game['has_prediction'] = has_opportunity
                                game['ai_confidence'] = extract_confidence_from_analysis(kairos_analysis)
                                game['opportunity_details'] = opportunity_details
                                
                                # Análise Gemini para TODOS os jogos (análise de movimentação de mercado)
                                try:
                                    game_context = {
                                        'teams': game.get('teams', 'N/A'),
                                        'league': game.get('league', 'N/A'),
                                        'datetime': game.get('datetime', 'N/A'),
                                        'status': 'live',
                                        'current_score': game.get('current_score', 'N/A'),
                                        'match_status': game.get('match_status', 'N/A')
                                    }
                                    
                                    print(f"🧠 Executando análise Gemini (movimentação de mercado)...")
                                    gemini_analysis = analyze_with_gemini(processed_markets, game_context)
                                    game['gemini_analysis'] = gemini_analysis
                                    print(f"✅ Análise Gemini concluída")
                                    
                                    # Verificar se Gemini identificou oportunidade adicional
                                    if gemini_analysis and "oportunidade" in gemini_analysis.lower():
                                        print(f"🎯 Gemini identificou possível oportunidade adicional!")
                                        
                                except Exception as e:
                                    print(f"⚠️ Erro na análise Gemini: {e}")
                                    game['gemini_analysis'] = None
                                
                                if has_opportunity:
                                    print(f"✅ OPORTUNIDADE IDENTIFICADA PELA KAIROS! Confiança: {game['ai_confidence']:.1f}%")
                                    
                                    # Criar relatório detalhado
                                    detailed_report = create_detailed_opportunity_report(game, opportunity_details, processed_markets)
                                    print(detailed_report)
                                    game['detailed_report'] = detailed_report
                                else:
                                    print(f"⚠️ KAIROS: Nenhuma oportunidade clara (Confiança: {game['ai_confidence']:.1f}%)")
                                
                                game['kairos_analysis'] = kairos_analysis
                                game['processed_markets'] = processed_markets
                                
                            else:
                                print("❌ Nenhum mercado processado")
                                game['has_prediction'] = False
                                game['ai_confidence'] = 0
                                
                        except Exception as e:
                            print(f"❌ Erro ao processar jogo individual: {e}")
                            game['has_prediction'] = False
                            game['ai_confidence'] = 0
                    else:
                        print("⚠️ Link da página individual não encontrado")
                        game['has_prediction'] = False
                        game['ai_confidence'] = 0
                    
                    processed_games.append(game)
                    
                    # Aguardar entre jogos para evitar sobrecarga
                    if i < min(5, len(games_data)):
                        await page.wait_for_timeout(2000)
                
                # Resumo final
                games_with_opportunities = [g for g in processed_games if g.get('has_prediction', False)]
                games_without_opportunities = [g for g in processed_games if not g.get('has_prediction', False)]
                
                print(f"\n" + "="*60)
                print(f"📊 RESUMO DA ANÁLISE KAIROS")
                print(f"="*60)
                print(f"🎯 Total de jogos analisados: {len(processed_games)}")
                print(f"✅ Jogos com oportunidades: {len(games_with_opportunities)}")
                print(f"❌ Jogos sem oportunidades: {len(games_without_opportunities)}")
                
                if games_with_opportunities:
                    print(f"\n🎯 OPORTUNIDADES IDENTIFICADAS:")
                    for i, game in enumerate(games_with_opportunities, 1):
                        confidence = game.get('ai_confidence', 0)
                        teams = game.get('teams', 'N/A')
                        league = game.get('league', 'N/A')
                        print(f"  {i}. {teams} ({league}) - Confiança: {confidence:.1f}%")
                
                if games_without_opportunities:
                    print(f"\n❌ JOGOS SEM OPORTUNIDADES CLARAS:")
                    for i, game in enumerate(games_without_opportunities, 1):
                        confidence = game.get('ai_confidence', 0)
                        teams = game.get('teams', 'N/A')
                        league = game.get('league', 'N/A')
                        print(f"  {i}. {teams} ({league}) - Confiança: {confidence:.1f}%")
                
                # Salvar resultados em arquivo JSON
                import json
                from datetime import datetime
                
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'total_games': len(processed_games),
                    'games_with_opportunities': len(games_with_opportunities),
                    'games_without_opportunities': len(games_without_opportunities),
                    'processed_games': processed_games
                }
                
                filename = f"kairos_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 Resultados salvos em: {filename}")
                
                return processed_games
                
            else:
                print("❌ Nenhum jogo ao vivo encontrado")
                return []
                
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Configurar proteções do browser
                await setup_browser_protection(context, page)
                
                # Navegar para a página principal
                print("🌐 Navegando para Excapper...")
                await page.goto("https://www.excapper.com/", timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
                await page.wait_for_timeout(3000)
                
                # Clicar no botão Live - tentar diferentes seletores
                print("🔴 Procurando botão Live...")
                
                # Aguardar carregamento completo
                await page.wait_for_timeout(5000)
                
                # Tentar diferentes seletores para o botão Live
                live_selectors = [
                    'a[href="/live"]',
                    'a[href="live"]', 
                    'a:has-text("Live")',
                    'a:has-text("LIVE")',
                    '.nav-link:has-text("Live")',
                    'button:has-text("Live")',
                    '[data-bs-target="#live"]'
                ]
                
                live_clicked = False
                for selector in live_selectors:
                    try:
                        live_button = page.locator(selector).first
                        if await live_button.is_visible(timeout=2000):
                            print(f"✅ Botão Live encontrado com seletor: {selector}")
                            await live_button.click()
                            live_clicked = True
                            break
                    except Exception as e:
                        print(f"⚠️ Seletor {selector} não funcionou: {e}")
                        continue
                
                if not live_clicked:
                    # Tentar navegar diretamente para a página live
                    print("🔄 Tentando navegar diretamente para /live...")
                    await page.goto("https://www.excapper.com/live", timeout=RATE_LIMIT_CONFIG['page_load_timeout'])
                
                await page.wait_for_timeout(5000)
                
                # Extrair dados dos jogos ao vivo
                print("📊 Extraindo dados dos jogos ao vivo...")
                live_games_data = await extract_live_games_data(page)
                
                if live_games_data:
                    print(f"\n✅ {len(live_games_data)} jogos encontrados!")
                    
                    # Processar jogos de forma segura com rate limiting
                    processed_games = await process_multiple_games_safely(live_games_data, page)
                    
                    # Relatório final
                    print(f"\n📋 RELATÓRIO FINAL:")
                    print(f"📊 Total de jogos processados: {len(processed_games)}")
                    
                    games_with_opportunities = [g for g in processed_games if g.get('has_prediction', False)]
                    games_without_opportunities = [g for g in processed_games if not g.get('has_prediction', False)]
                    
                    print(f"✅ Jogos com oportunidades: {len(games_with_opportunities)}")
                    print(f"⚠️ Jogos sem oportunidades: {len(games_without_opportunities)}")
                    
                    if games_with_opportunities:
                        print(f"\n🎯 JOGOS COM PROGNÓSTICOS:")
                        for i, game in enumerate(games_with_opportunities, 1):
                            confidence = game.get('ai_confidence', 0)
                            teams = game.get('teams', 'N/A')
                            league = game.get('league', 'N/A')
                            print(f"  {i}. {teams} ({league}) - Confiança: {confidence:.1f}%")
                    
                    if games_without_opportunities:
                        print(f"\n⚠️ JOGOS SEM PROGNÓSTICOS (baixa confiança ou sem oportunidade):")
                        for i, game in enumerate(games_without_opportunities, 1):
                            confidence = game.get('ai_confidence', 0)
                            teams = game.get('teams', 'N/A')
                            league = game.get('league', 'N/A')
                            print(f"  {i}. {teams} ({league}) - Confiança: {confidence:.1f}%")
                    
                    # Salvar resultados em arquivo JSON
                    import json
                    from datetime import datetime
                    
                    results = {
                        'timestamp': datetime.now().isoformat(),
                        'total_games': len(processed_games),
                        'games_with_opportunities': len(games_with_opportunities),
                        'games_without_opportunities': len(games_without_opportunities),
                        'processed_games': processed_games
                    }
                    
                    filename = f"kairos_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    
                    print(f"\n💾 Resultados salvos em: {filename}")
                    
                else:
                    print("❌ Nenhum jogo ao vivo encontrado")
                    
            except Exception as e:
                print(f"❌ Erro durante a execução: {e}")
            finally:
                await browser.close()
    
    asyncio.run(main())