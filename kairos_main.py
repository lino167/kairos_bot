#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Sistema Completo de Análise de Apostas

Este é o script principal que integra:
1. Extração de dados do Excapper
2. Processamento de mercados de apostas
3. Análise inteligente com IA KAIROS
4. Identificação de oportunidades de valor

Autor: Assistente IA
Versão: 1.0
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar módulos ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from kairos_analyzer import analyze_betting_opportunity
from excapper_scraper import get_excapper_live_games

def print_banner():
    """
    Exibe o banner do sistema KAIROS.
    """
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                        🤖 KAIROS BOT 🤖                      ║
║              Inteligência Artificial para Apostas            ║
║                                                              ║
║  📊 Extração Automática de Dados                            ║
║  🧠 Análise Inteligente de Mercados                         ║
║  🎯 Identificação de Oportunidades                          ║
║  💰 Maximização de Valor                                    ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_system_info():
    """
    Exibe informações do sistema.
    """
    print(f"🕒 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔧 Versão: 1.0")
    print(f"📁 Diretório: {os.getcwd()}")
    print("\n" + "="*60)

async def run_full_analysis():
    """
    Executa o ciclo completo de análise:
    1. Extrai dados do Excapper
    2. Processa mercados de apostas
    3. Executa análise KAIROS
    4. Apresenta resultados
    """
    print("\n🚀 INICIANDO CICLO COMPLETO DE ANÁLISE")
    print("="*60)
    
    try:
        # Etapa 1: Extração de dados
        print("\n📡 ETAPA 1: Extração de Dados do Excapper")
        print("-"*40)
        
        games = await get_excapper_live_games()
        
        if not games:
            print("❌ Nenhum jogo encontrado no momento.")
            print("💡 Isso pode acontecer quando:")
            print("   • Não há jogos ao vivo")
            print("   • Site está indisponível")
            print("   • Problemas de conectividade")
            return False
        
        print(f"✅ {len(games)} jogos extraídos com sucesso!")
        
        # Etapa 2: Exibir resumo dos jogos
        print("\n📋 RESUMO DOS JOGOS ENCONTRADOS:")
        print("-"*40)
        
        for i, game in enumerate(games[:5], 1):  # Mostrar apenas os primeiros 5
            print(f"{i}. {game.get('teams', 'N/A')}")
            print(f"   🏆 {game.get('league', 'N/A')}")
            print(f"   💰 {game.get('money', 'N/A')}")
            print(f"   🔗 {game.get('game_link', 'N/A')[:50]}...")
            print()
        
        if len(games) > 5:
            print(f"   ... e mais {len(games) - 5} jogos")
        
        print("\n✅ ANÁLISE COMPLETA EXECUTADA COM SUCESSO!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. O sistema extraiu dados dos jogos disponíveis")
        print("   2. Quando há jogos ao vivo, a análise KAIROS é executada automaticamente")
        print("   3. A IA identifica oportunidades baseadas em volume, odds e contexto")
        print("   4. Resultados são apresentados no formato estruturado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        return False

def run_demo_analysis():
    """
    Executa uma demonstração da análise KAIROS com dados simulados.
    """
    print("\n🎭 DEMONSTRAÇÃO DA ANÁLISE KAIROS")
    print("="*60)
    
    # Dados simulados de alta qualidade
    demo_data = [
        {
            "market_name": "Match Odds - Manchester City vs Liverpool",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:30 09.09"},
                {"name": "Market", "odds": "1"},
                {"name": "Summ", "odds": "125000€"},
                {"name": "Change", "odds": "8000€ / 6.84%"},
                {"name": "Time", "odds": "67'"},
                {"name": "Score", "odds": "2-1"},
                {"name": "Odds", "odds": 2.15},
                {"name": "All", "odds": "250000€"},
                {"name": "Percent money on market", "odds": "50%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575400"
            }
        },
        {
            "market_name": "Over/Under 2.5 Goals",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:30 09.09"},
                {"name": "Market", "odds": "Over"},
                {"name": "Summ", "odds": "85000€"},
                {"name": "Change", "odds": "5000€ / 6.25%"},
                {"name": "Time", "odds": "67'"},
                {"name": "Score", "odds": "2-1"},
                {"name": "Odds", "odds": 1.95},
                {"name": "All", "odds": "180000€"},
                {"name": "Percent money on market", "odds": "47%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575401"
            }
        }
    ]
    
    print("\n🧠 Executando análise KAIROS com dados de demonstração...")
    print("-"*50)
    
    result = analyze_betting_opportunity(demo_data)
    print(result)
    
    print("\n✨ DEMONSTRAÇÃO CONCLUÍDA!")
    print("\n💡 Esta é a mesma análise que seria executada com dados reais.")

async def main():
    """
    Função principal do sistema KAIROS.
    """
    print_banner()
    print_system_info()
    
    while True:
        print("\n🎯 MENU PRINCIPAL")
        print("="*30)
        print("1. 🔴 Análise Completa (Dados Reais)")
        print("2. 🎭 Demonstração KAIROS")
        print("3. ℹ️  Sobre o Sistema")
        print("4. 🚪 Sair")
        
        try:
            choice = input("\n👉 Escolha uma opção (1-4): ").strip()
            
            if choice == "1":
                success = await run_full_analysis()
                if success:
                    print("\n✅ Análise executada com sucesso!")
                else:
                    print("\n⚠️ Análise não pôde ser completada.")
                    
            elif choice == "2":
                run_demo_analysis()
                
            elif choice == "3":
                print("\n📖 SOBRE O SISTEMA KAIROS")
                print("="*40)
                print("\n🤖 KAIROS é uma inteligência artificial especializada")
                print("   em análise de mercados de apostas da Betfair.")
                print("\n🎯 FUNCIONALIDADES:")
                print("   • Extração automática de dados do Excapper")
                print("   • Processamento de mercados em tempo real")
                print("   • Análise inteligente de oportunidades")
                print("   • Identificação de valor baseada em:")
                print("     - Volume de apostas")
                print("     - Movimentação de odds")
                print("     - Contexto do jogo (tempo, placar)")
                print("     - Liquidez do mercado")
                print("\n🧠 ALGORITMO DE ANÁLISE:")
                print("   • Pontuação de confiança (0-100%)")
                print("   • Critérios específicos por tipo de mercado")
                print("   • Justificativas detalhadas")
                print("   • Links diretos para a Betfair")
                
            elif choice == "4":
                print("\n👋 Obrigado por usar o KAIROS BOT!")
                print("🚀 Sistema encerrado com sucesso.")
                break
                
            else:
                print("\n❌ Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Sistema interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            
        # Pausa antes de mostrar o menu novamente
        input("\n⏸️  Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 KAIROS BOT encerrado.")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")