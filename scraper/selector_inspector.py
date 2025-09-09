#!/usr/bin/env python3
"""
Script de Investigação de Seletores - Excapper

Este script é usado para encontrar os seletores CSS exatos
para o botão 'Live' e para a tabela de jogos no site Excapper.

Autor: Kairos Bot
Data: 2025
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def inspect_excapper_selectors():
    """
    Investiga e encontra os seletores CSS para elementos do Excapper.
    
    Returns:
        dict: Dicionário com os seletores encontrados
    """
    selectors_found = {
        'timestamp': datetime.now().isoformat(),
        'url': 'https://www.excapper.com/',
        'live_button': None,
        'games_table': None,
        'game_rows': None,
        'additional_elements': []
    }
    
    async with async_playwright() as p:
        # Iniciar navegador em modo headless (oculto)
        browser = await p.chromium.launch(headless=True, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            print("🔍 Navegando para o Excapper...")
            await page.goto('https://www.excapper.com/', wait_until='networkidle')
            
            # Aguardar um pouco para a página carregar completamente
            await page.wait_for_timeout(3000)
            
            print("🔍 Procurando pelo botão 'Live'...")
            
            # Possíveis seletores para o botão Live
            live_button_selectors = [
                'a[href*="live"]',
                'button:has-text("Live")',
                'a:has-text("Live")',
                '[data-testid*="live"]',
                '.live-button',
                '#live-button',
                'nav a:has-text("Live")',
                '.menu a:has-text("Live")',
                '.navigation a:has-text("Live")',
                'a[title*="Live"]',
                'button[title*="Live"]'
            ]
            
            # Testar cada seletor para o botão Live
            for selector in live_button_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        href = await element.get_attribute('href') if await element.get_attribute('href') else 'N/A'
                        print(f"✅ Botão Live encontrado: {selector}")
                        print(f"   Texto: '{text.strip()}'")
                        print(f"   Href: {href}")
                        selectors_found['live_button'] = {
                            'selector': selector,
                            'text': text.strip(),
                            'href': href
                        }
                        break
                except Exception as e:
                    continue
            
            # Se encontrou o botão Live, tentar clicar nele
            if selectors_found['live_button']:
                print(f"🖱️ Clicando no botão Live...")
                try:
                    await page.click(selectors_found['live_button']['selector'])
                    await page.wait_for_timeout(3000)  # Aguardar navegação
                    print("✅ Clique realizado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao clicar: {e}")
            
            print("🔍 Procurando pela tabela de jogos...")
            
            # Possíveis seletores para a tabela de jogos
            table_selectors = [
                'table',
                '.games-table',
                '.matches-table',
                '.live-games',
                '.odds-table',
                '[data-testid*="table"]',
                '[data-testid*="games"]',
                '.table-responsive table',
                '.content table',
                'div[class*="table"]',
                'div[class*="games"]',
                'div[class*="matches"]'
            ]
            
            # Testar cada seletor para a tabela
            for selector in table_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ Tabela encontrada: {selector} ({len(elements)} elemento(s))")
                        
                        # Pegar informações da primeira tabela
                        first_table = elements[0]
                        rows = await first_table.query_selector_all('tr')
                        print(f"   Linhas na tabela: {len(rows)}")
                        
                        selectors_found['games_table'] = {
                            'selector': selector,
                            'count': len(elements),
                            'rows_count': len(rows)
                        }
                        
                        # Tentar encontrar seletores para as linhas de jogos
                        if rows:
                            row_selectors = [
                                f"{selector} tr",
                                f"{selector} tbody tr",
                                f"{selector} tr:not(:first-child)",
                                f"{selector} .game-row",
                                f"{selector} .match-row"
                            ]
                            
                            for row_selector in row_selectors:
                                try:
                                    game_rows = await page.query_selector_all(row_selector)
                                    if len(game_rows) > 1:  # Mais de uma linha (excluindo cabeçalho)
                                        selectors_found['game_rows'] = {
                                            'selector': row_selector,
                                            'count': len(game_rows)
                                        }
                                        print(f"   Linhas de jogos: {row_selector} ({len(game_rows)} linhas)")
                                        break
                                except:
                                    continue
                        break
                except Exception as e:
                    continue
            
            # Procurar por outros elementos interessantes
            print("🔍 Procurando por outros elementos relevantes...")
            
            other_selectors = {
                'odds_elements': ['[class*="odd"]', '.odds', '[data-odd]'],
                'team_names': ['[class*="team"]', '.team', '[class*="match"]'],
                'time_elements': ['[class*="time"]', '.time', '[datetime]'],
                'league_elements': ['[class*="league"]', '.league', '[class*="competition"]']
            }
            
            for element_type, selectors in other_selectors.items():
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            selectors_found['additional_elements'].append({
                                'type': element_type,
                                'selector': selector,
                                'count': len(elements)
                            })
                            print(f"   {element_type}: {selector} ({len(elements)} elementos)")
                            break
                    except:
                        continue
            
            # Salvar screenshot para análise
            screenshot_path = f"screenshots/selector_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot salvo: {screenshot_path}")
            
            # Salvar HTML da página para análise offline
            html_content = await page.content()
            html_path = f"data/excapper_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"💾 HTML salvo: {html_path}")
            
        except Exception as e:
            print(f"❌ Erro durante a investigação: {e}")
        
        finally:
            await browser.close()
    
    return selectors_found


async def main():
    """
    Função principal para executar a investigação de seletores.
    """
    print("🚀 Iniciando investigação de seletores do Excapper...")
    print("📋 Este script irá:")
    print("   1. Navegar para o site Excapper")
    print("   2. Procurar pelo botão 'Live'")
    print("   3. Clicar no botão (se encontrado)")
    print("   4. Procurar pela tabela de jogos")
    print("   5. Identificar seletores para linhas de jogos")
    print("   6. Salvar screenshot e HTML para análise")
    print("\n" + "="*50 + "\n")
    
    selectors = await inspect_excapper_selectors()
    
    # Salvar resultados em JSON
    results_path = f"data/selectors_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(selectors, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*50)
    print("📊 RESULTADOS DA INVESTIGAÇÃO:")
    print("="*50)
    
    if selectors['live_button']:
        print(f"✅ Botão Live: {selectors['live_button']['selector']}")
        print(f"   Texto: '{selectors['live_button']['text']}'")
        print(f"   Link: {selectors['live_button']['href']}")
    else:
        print("❌ Botão Live não encontrado")
    
    if selectors['games_table']:
        print(f"✅ Tabela de jogos: {selectors['games_table']['selector']}")
        print(f"   Quantidade: {selectors['games_table']['count']}")
        print(f"   Linhas: {selectors['games_table']['rows_count']}")
    else:
        print("❌ Tabela de jogos não encontrada")
    
    if selectors['game_rows']:
        print(f"✅ Linhas de jogos: {selectors['game_rows']['selector']}")
        print(f"   Quantidade: {selectors['game_rows']['count']}")
    else:
        print("❌ Linhas de jogos não encontradas")
    
    if selectors['additional_elements']:
        print("\n📋 Elementos adicionais encontrados:")
        for element in selectors['additional_elements']:
            print(f"   {element['type']}: {element['selector']} ({element['count']} elementos)")
    
    print(f"\n💾 Resultados salvos em: {results_path}")
    print("\n🎯 Use estes seletores no arquivo excapper_scraper.py!")


if __name__ == "__main__":
    asyncio.run(main())