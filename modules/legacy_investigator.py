#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Investigação Avançada com Playwright - Kairos Bot
Analisa o site excapper.com usando automação de navegador para capturar conteúdo dinâmico
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class PlaywrightExcapperInvestigator:
    def __init__(self):
        self.base_url = "https://www.excapper.com/"
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    async def setup_browser(self, playwright, headless=True):
        """Configura o navegador com as opções necessárias"""
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Adiciona headers extras
        await context.set_extra_http_headers({
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return browser, context
    
    async def capture_page_info(self, page):
        """Captura informações básicas da página"""
        info = {
            'url': page.url,
            'title': await page.title(),
            'viewport': page.viewport_size,
            'user_agent': await page.evaluate('navigator.userAgent'),
            'timestamp': datetime.now().isoformat()
        }
        return info
    
    async def wait_for_content_load(self, page, timeout=10000):
        """Aguarda o carregamento completo do conteúdo dinâmico"""
        try:
            # Aguarda elementos específicos que indicam carregamento completo
            await page.wait_for_selector('table', timeout=timeout)
            
            # Aguarda um pouco mais para JavaScript executar
            await page.wait_for_timeout(2000)
            
            # Verifica se há elementos com dados de apostas
            await page.wait_for_function(
                "document.querySelectorAll('td').length > 10",
                timeout=timeout
            )
            
            print("✅ Conteúdo carregado completamente")
            return True
            
        except Exception as e:
            print(f"⚠️ Timeout aguardando conteúdo: {e}")
            return False
    
    async def extract_dynamic_content(self, page):
        """Extrai conteúdo que pode ser carregado dinamicamente"""
        # Aguarda carregamento
        await self.wait_for_content_load(page)
        
        # Executa JavaScript para obter dados dinâmicos
        dynamic_data = await page.evaluate("""
            () => {
                const data = {
                    tables: [],
                    ajax_calls: [],
                    websockets: [],
                    local_storage: {},
                    session_storage: {},
                    cookies: document.cookie,
                    scripts_loaded: []
                };
                
                // Analisa tabelas
                document.querySelectorAll('table').forEach((table, index) => {
                    const rows = Array.from(table.querySelectorAll('tr')).map(row => {
                        return Array.from(row.querySelectorAll('td, th')).map(cell => 
                            cell.textContent.trim()
                        );
                    });
                    
                    data.tables.push({
                        index: index,
                        rows: rows.length,
                        columns: rows[0] ? rows[0].length : 0,
                        sample_data: rows.slice(0, 3)
                    });
                });
                
                // Verifica localStorage
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        data.local_storage[key] = localStorage.getItem(key);
                    }
                } catch (e) {}
                
                // Verifica sessionStorage
                try {
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        data.session_storage[key] = sessionStorage.getItem(key);
                    }
                } catch (e) {}
                
                // Lista scripts carregados
                document.querySelectorAll('script[src]').forEach(script => {
                    data.scripts_loaded.push(script.src);
                });
                
                return data;
            }
        """)
        
        return dynamic_data
    
    async def extract_betting_tables(self, page):
        """Extrai dados específicos das tabelas de apostas"""
        betting_data = await page.evaluate("""
            () => {
                const tables = [];
                
                document.querySelectorAll('table').forEach((table, tableIndex) => {
                    const tableData = {
                        index: tableIndex,
                        headers: [],
                        rows: []
                    };
                    
                    // Extrai cabeçalhos
                    const headerCells = table.querySelectorAll('th');
                    headerCells.forEach(th => {
                        tableData.headers.push(th.textContent.trim());
                    });
                    
                    // Extrai dados das linhas
                    const dataRows = table.querySelectorAll('tr');
                    dataRows.forEach((row, rowIndex) => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length > 0) {
                            const rowData = [];
                            cells.forEach(cell => {
                                rowData.push({
                                    text: cell.textContent.trim(),
                                    html: cell.innerHTML,
                                    classes: Array.from(cell.classList),
                                    attributes: Array.from(cell.attributes).reduce((acc, attr) => {
                                        acc[attr.name] = attr.value;
                                        return acc;
                                    }, {})
                                });
                            });
                            tableData.rows.push(rowData);
                        }
                    });
                    
                    tables.push(tableData);
                });
                
                return tables;
            }
        """)
        
        return betting_data
    
    async def monitor_network_activity(self, page):
        """Monitora atividade de rede para identificar chamadas AJAX/API"""
        network_calls = []
        
        async def handle_request(request):
            if request.url != self.base_url:
                network_calls.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'timestamp': datetime.now().isoformat()
                })
        
        async def handle_response(response):
            if response.url != self.base_url and response.status != 200:
                print(f"⚠️ Resposta não-200: {response.status} - {response.url}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        return network_calls
    
    async def take_screenshots(self, page):
        """Captura screenshots da página"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Screenshot da página completa
        full_screenshot = self.screenshots_dir / f"full_page_{timestamp}.png"
        await page.screenshot(path=str(full_screenshot), full_page=True)
        
        # Screenshot da viewport atual
        viewport_screenshot = self.screenshots_dir / f"viewport_{timestamp}.png"
        await page.screenshot(path=str(viewport_screenshot))
        
        print(f"📸 Screenshots salvos: {full_screenshot.name}, {viewport_screenshot.name}")
        
        return {
            'full_page': str(full_screenshot),
            'viewport': str(viewport_screenshot)
        }
    
    async def interact_with_page(self, page):
        """Interage com elementos da página para revelar conteúdo dinâmico"""
        interactions = []
        
        try:
            # Procura por abas ou botões que podem carregar mais conteúdo
            tabs = await page.query_selector_all('[role="tab"], .tab, .nav-link')
            for i, tab in enumerate(tabs[:3]):  # Limita a 3 abas
                try:
                    tab_text = await tab.text_content()
                    print(f"🔄 Clicando na aba: {tab_text}")
                    
                    await tab.click()
                    await page.wait_for_timeout(2000)  # Aguarda carregamento
                    
                    interactions.append({
                        'type': 'tab_click',
                        'element': tab_text,
                        'index': i
                    })
                    
                except Exception as e:
                    print(f"⚠️ Erro ao clicar na aba {i}: {e}")
            
            # Procura por botões de "Load More" ou similares
            load_buttons = await page.query_selector_all('button:has-text("Load"), button:has-text("More"), .load-more')
            for button in load_buttons[:2]:  # Limita a 2 botões
                try:
                    button_text = await button.text_content()
                    print(f"🔄 Clicando no botão: {button_text}")
                    
                    await button.click()
                    await page.wait_for_timeout(3000)
                    
                    interactions.append({
                        'type': 'button_click',
                        'element': button_text
                    })
                    
                except Exception as e:
                    print(f"⚠️ Erro ao clicar no botão: {e}")
        
        except Exception as e:
            print(f"⚠️ Erro durante interações: {e}")
        
        return interactions
    
    async def run_investigation(self, headless=True):
        """Executa a investigação completa com Playwright"""
        print("=" * 70)
        print("KAIROS BOT - INVESTIGAÇÃO AVANÇADA COM PLAYWRIGHT")
        print("=" * 70)
        
        async with async_playwright() as playwright:
            browser, context = await self.setup_browser(playwright, headless)
            page = await context.new_page()
            
            try:
                # Monitora atividade de rede
                network_calls = await self.monitor_network_activity(page)
                
                print(f"🌐 Navegando para: {self.base_url}")
                await page.goto(self.base_url, wait_until='networkidle')
                
                # Captura informações básicas
                page_info = await self.capture_page_info(page)
                print(f"📄 Título: {page_info['title']}")
                print(f"🔗 URL: {page_info['url']}")
                
                # Aguarda e extrai conteúdo dinâmico
                print("\n⏳ Aguardando carregamento do conteúdo dinâmico...")
                dynamic_content = await self.extract_dynamic_content(page)
                
                # Interage com a página
                print("\n🔄 Interagindo com elementos da página...")
                interactions = await self.interact_with_page(page)
                
                # Extrai dados das tabelas de apostas
                print("\n📊 Extraindo dados das tabelas de apostas...")
                betting_tables = await self.extract_betting_tables(page)
                
                # Captura screenshots
                print("\n📸 Capturando screenshots...")
                screenshots = await self.take_screenshots(page)
                
                # Obtém HTML final
                final_html = await page.content()
                
                # Compila relatório completo
                report = {
                    'page_info': page_info,
                    'dynamic_content': dynamic_content,
                    'betting_tables': betting_tables,
                    'interactions': interactions,
                    'network_calls': network_calls,
                    'screenshots': screenshots,
                    'html_size': len(final_html),
                    'investigation_timestamp': datetime.now().isoformat()
                }
                
                # Salva HTML final
                with open('playwright_page.html', 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                # Salva relatório
                with open('playwright_report.json', 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                # Exibe resumo
                self.print_summary(report)
                
            except Exception as e:
                print(f"❌ Erro durante investigação: {e}")
                
            finally:
                await browser.close()
        
        print("\n" + "=" * 70)
        print("INVESTIGAÇÃO COM PLAYWRIGHT CONCLUÍDA")
        print("=" * 70)
    
    def print_summary(self, report):
        """Exibe resumo dos resultados"""
        print("\n" + "=" * 50)
        print("RESUMO DA INVESTIGAÇÃO")
        print("=" * 50)
        
        # Informações da página
        print(f"📄 Título: {report['page_info']['title']}")
        print(f"🔗 URL: {report['page_info']['url']}")
        print(f"📏 Tamanho HTML: {report['html_size']:,} caracteres")
        
        # Conteúdo dinâmico
        dynamic = report['dynamic_content']
        print(f"\n📊 Tabelas encontradas: {len(dynamic['tables'])}")
        for i, table in enumerate(dynamic['tables']):
            print(f"  - Tabela {i}: {table['rows']} linhas, {table['columns']} colunas")
        
        # Dados de apostas
        print(f"\n🎯 Tabelas de apostas detalhadas: {len(report['betting_tables'])}")
        for i, table in enumerate(report['betting_tables']):
            if table['headers']:
                print(f"  - Tabela {i}: {table['headers']}")
            print(f"    Linhas de dados: {len(table['rows'])}")
        
        # Atividade de rede
        print(f"\n🌐 Chamadas de rede capturadas: {len(report['network_calls'])}")
        
        # Interações
        print(f"\n🔄 Interações realizadas: {len(report['interactions'])}")
        
        # Storage
        storage_items = len(dynamic.get('local_storage', {})) + len(dynamic.get('session_storage', {}))
        print(f"\n💾 Itens em storage: {storage_items}")
        
        print(f"\n📸 Screenshots salvos em: {Path('screenshots').absolute()}")
        print(f"📄 Relatório salvo em: playwright_report.json")
        print(f"🌐 HTML salvo em: playwright_page.html")

async def main():
    investigator = PlaywrightExcapperInvestigator()
    await investigator.run_investigation(headless=True)

if __name__ == "__main__":
    asyncio.run(main())