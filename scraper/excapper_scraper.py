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
from playwright.async_api import async_playwright


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
            
            # Encontrar e clicar no botão 'Live'
            print("🔍 Procurando pelo botão Live...")
            live_button_selector = 'a[href*="live"]'
            
            try:
                await page.wait_for_selector(live_button_selector, timeout=10000)
                await page.click(live_button_selector)
                print("✅ Botão Live clicado com sucesso!")
                
                # Aguardar a navegação/atualização da página
                await page.wait_for_timeout(3000)
                
            except Exception as e:
                print(f"❌ Erro ao clicar no botão Live: {e}")
                return []
            
            # Verificar se a tabela de jogos está presente
            print("🔍 Verificando tabela de jogos...")
            table_selector = 'table'
            
            # Aguardar um pouco para a página carregar completamente
            await page.wait_for_timeout(2000)
            
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
                
                # Filtrar apenas jogos com sinais de oportunidade (opcional)
                opportunities = [game for game in games_data if game.get('opportunity_signal')]
                
                if opportunities:
                    print(f"🎯 Encontradas {len(opportunities)} oportunidades!")
                    return opportunities
                else:
                    print("📊 Retornando todos os jogos encontrados")
                    return games_data[:10]  # Limitar a 10 para teste
                
            except Exception as e:
                print(f"❌ Erro ao extrair dados da tabela: {e}")
                return []
            
        except Exception as e:
            print(f"Erro durante a extração: {e}")
            return []
        
        finally:
            await browser.close()


if __name__ == "__main__":
    # Função para testar o scraper
    async def main():
        print("Iniciando extração de dados do Excapper...")
        games = await get_excapper_live_games()
        print(f"Jogos encontrados: {len(games)}")
        for game in games:
            print(f"- {game}")
    
    asyncio.run(main())