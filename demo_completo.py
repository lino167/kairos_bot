#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Demonstração Completa
==================================

Este script demonstra todas as funcionalidades do sistema KAIROS:
1. Extração de dados do Excapper
2. Processamento de mercados de apostas
3. Análise KAIROS local
4. Análise avançada com Gemini AI
5. Identificação de oportunidades

Autor: KAIROS Team
Versão: 2.0
Data: Janeiro 2025
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do sistema
from scraper.excapper_scraper import get_excapper_live_games
from modules.kairos_analyzer import analyze_betting_opportunity
from modules.gemini_analyzer import analyze_with_gemini
from config.api_keys import validate_gemini_key, get_gemini_api_key

def print_header():
    """Exibe o cabeçalho do sistema."""
    print("\n" + "="*60)
    print("🤖 KAIROS BOT - Sistema Inteligente de Análise de Apostas")
    print("="*60)
    print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔑 Gemini AI: {'✅ Ativo' if validate_gemini_key() else '❌ Inativo'}")
    print("="*60)

def print_system_status():
    """Exibe o status dos componentes do sistema."""
    print("\n🔧 STATUS DOS COMPONENTES:")
    print("-" * 30)
    
    # Verificar Gemini
    gemini_status = "✅ Operacional" if validate_gemini_key() else "❌ Indisponível"
    print(f"🧠 Gemini AI: {gemini_status}")
    
    # Verificar módulos
    try:
        from modules.kairos_analyzer import analyze_betting_opportunity
        kairos_status = "✅ Operacional"
    except ImportError:
        kairos_status = "❌ Erro de importação"
    print(f"🎯 KAIROS Analyzer: {kairos_status}")
    
    try:
        from scraper.excapper_scraper import get_excapper_live_games
        scraper_status = "✅ Operacional"
    except ImportError:
        scraper_status = "❌ Erro de importação"
    print(f"🕷️ Excapper Scraper: {scraper_status}")
    
    print("-" * 30)

async def demo_completa():
    """Executa uma demonstração completa do sistema."""
    print_header()
    print_system_status()
    
    print("\n🚀 INICIANDO DEMONSTRAÇÃO COMPLETA...")
    print("\n📊 Fase 1: Extração de Dados do Excapper")
    print("-" * 40)
    
    try:
        # Extrair dados do Excapper
        live_games = await get_excapper_live_games()
        
        if live_games:
            print(f"✅ {len(live_games)} jogos extraídos com sucesso!")
            
            # Mostrar alguns jogos encontrados
            print("\n🎮 JOGOS ENCONTRADOS (Primeiros 5):")
            for i, game in enumerate(live_games[:5], 1):
                print(f"{i}. {game.get('teams', 'N/A')} - {game.get('league', 'N/A')}")
                print(f"   💰 Volume: {game.get('money', 'N/A')}")
                print(f"   🎯 Sinal: {game.get('opportunity_signal', 'Nenhum')}")
                print()
            
            # Demonstrar análises com dados reais (se disponíveis)
            if live_games:
                print("\n📊 Fase 2: Análise KAIROS")
                print("-" * 40)
                
                # Criar dados simulados baseados nos jogos reais
                sample_markets = [
                    {
                        'market_name': 'Match Odds',
                        'market_type': 'live',
                        'total_volume': 50000,
                        'selections': [
                            {'name': 'Home', 'odds': 2.1, 'volume': 25000},
                            {'name': 'Draw', 'odds': 3.2, 'volume': 15000},
                            {'name': 'Away', 'odds': 3.8, 'volume': 10000}
                        ]
                    },
                    {
                        'market_name': 'Over/Under 2.5 Goals',
                        'market_type': 'live',
                        'total_volume': 30000,
                        'selections': [
                            {'name': 'Over 2.5', 'odds': 1.8, 'volume': 20000},
                            {'name': 'Under 2.5', 'odds': 2.0, 'volume': 10000}
                        ]
                    }
                ]
                
                # Análise KAIROS local
                print("🤖 Executando análise KAIROS local...")
                kairos_result = analyze_betting_opportunity(sample_markets)
                print(kairos_result)
                
                # Análise Gemini (se disponível)
                if validate_gemini_key():
                    print("\n🧠 Executando análise Gemini AI...")
                    game_context = {
                        'teams': live_games[0].get('teams', 'N/A'),
                        'league': live_games[0].get('league', 'N/A'),
                        'datetime': live_games[0].get('datetime', 'N/A'),
                        'status': 'live'
                    }
                    
                    gemini_result = analyze_with_gemini(sample_markets, game_context)
                    print(gemini_result)
                else:
                    print("\n⚠️ Análise Gemini não disponível (chave API não configurada)")
                
        else:
            print("❌ Nenhum jogo encontrado no momento")
            print("\n🎭 Executando demonstração com dados simulados...")
            await demo_dados_simulados()
            
    except Exception as e:
        print(f"❌ Erro durante a extração: {e}")
        print("\n🎭 Executando demonstração com dados simulados...")
        await demo_dados_simulados()
    
    print("\n" + "="*60)
    print("✅ DEMONSTRAÇÃO COMPLETA FINALIZADA!")
    print("="*60)

async def demo_dados_simulados():
    """Demonstração com dados simulados."""
    print("\n📊 DEMONSTRAÇÃO COM DADOS SIMULADOS")
    print("-" * 40)
    
    # Dados simulados de mercados
    sample_markets = [
        {
            'market_name': 'Match Odds',
            'market_type': 'live',
            'total_volume': 75000,
            'selections': [
                {'name': 'Manchester City', 'odds': 1.5, 'volume': 45000},
                {'name': 'Draw', 'odds': 4.2, 'volume': 15000},
                {'name': 'Liverpool', 'odds': 6.0, 'volume': 15000}
            ]
        },
        {
            'market_name': 'Over/Under 2.5 Goals',
            'market_type': 'live',
            'total_volume': 40000,
            'selections': [
                {'name': 'Over 2.5', 'odds': 1.9, 'volume': 28000},
                {'name': 'Under 2.5', 'odds': 1.95, 'volume': 12000}
            ]
        },
        {
            'market_name': 'Both Teams to Score',
            'market_type': 'live',
            'total_volume': 25000,
            'selections': [
                {'name': 'Yes', 'odds': 1.7, 'volume': 18000},
                {'name': 'No', 'odds': 2.1, 'volume': 7000}
            ]
        }
    ]
    
    # Análise KAIROS
    print("🤖 Executando análise KAIROS...")
    kairos_result = analyze_betting_opportunity(sample_markets)
    print(kairos_result)
    
    # Análise Gemini (se disponível)
    if validate_gemini_key():
        print("\n🧠 Executando análise Gemini AI...")
        game_context = {
            'teams': 'Manchester City vs Liverpool',
            'league': 'Premier League',
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'status': 'live'
        }
        
        gemini_result = analyze_with_gemini(sample_markets, game_context)
        print(gemini_result)
    else:
        print("\n⚠️ Análise Gemini não disponível")

def menu_principal():
    """Exibe o menu principal."""
    while True:
        print("\n" + "="*50)
        print("🤖 KAIROS BOT - MENU PRINCIPAL")
        print("="*50)
        print("1. 🚀 Demonstração Completa (Dados Reais)")
        print("2. 🎭 Demonstração com Dados Simulados")
        print("3. 🔧 Verificar Status do Sistema")
        print("4. 🧠 Testar Gemini AI")
        print("5. ❌ Sair")
        print("="*50)
        
        escolha = input("\n👉 Escolha uma opção (1-5): ").strip()
        
        if escolha == '1':
            print("\n🚀 Iniciando demonstração completa...")
            asyncio.run(demo_completa())
        elif escolha == '2':
            print("\n🎭 Iniciando demonstração simulada...")
            asyncio.run(demo_dados_simulados())
        elif escolha == '3':
            print_system_status()
        elif escolha == '4':
            testar_gemini()
        elif escolha == '5':
            print("\n👋 Obrigado por usar o KAIROS BOT!")
            break
        else:
            print("\n❌ Opção inválida! Tente novamente.")

def testar_gemini():
    """Testa a integração com Gemini AI."""
    print("\n🧠 TESTANDO GEMINI AI")
    print("-" * 30)
    
    if validate_gemini_key():
        key = get_gemini_api_key()
        print(f"✅ Chave API: {key[:10]}...{key[-5:]}")
        print("✅ Gemini AI está configurado e pronto para uso!")
        
        # Teste rápido
        try:
            from modules.gemini_analyzer import GeminiAnalyzer
            analyzer = GeminiAnalyzer()
            print("✅ Analyzer inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar analyzer: {e}")
    else:
        print("❌ Chave API do Gemini não configurada")
        print("💡 Configure a chave em config/api_keys.py")

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Sistema encerrado pelo usuário. Até logo!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("🔧 Verifique a configuração do sistema e tente novamente.")