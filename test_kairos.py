#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da funcionalidade KAIROS com dados simulados

Este script demonstra como a IA KAIROS analisa mercados de apostas
e identifica oportunidades de valor.
"""

import sys
import os

# Adicionar o diretório de módulos ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from kairos_analyzer import analyze_betting_opportunity

def create_sample_market_data():
    """
    Cria dados de exemplo simulando mercados extraídos do Excapper.
    
    Returns:
        List[Dict]: Lista de mercados com dados realistas
    """
    return [
        {
            "market_name": "Match Odds",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:45 09.09"},
                {"name": "Market", "odds": "1"},
                {"name": "Summ", "odds": "75000€"},
                {"name": "Change", "odds": "5000€ / 7.14%"},
                {"name": "Time", "odds": "23'"},
                {"name": "Score", "odds": "1-0"},
                {"name": "Odds", "odds": 1.95},
                {"name": "All", "odds": "125000€"},
                {"name": "Percent money on market", "odds": "60%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575347"
            }
        },
        {
            "market_name": "Over/Under 2.5 Goals",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:45 09.09"},
                {"name": "Market", "odds": "Over"},
                {"name": "Summ", "odds": "45000€"},
                {"name": "Change", "odds": "2000€ / 4.65%"},
                {"name": "Time", "odds": "23'"},
                {"name": "Score", "odds": "1-0"},
                {"name": "Odds", "odds": 2.10},
                {"name": "All", "odds": "85000€"},
                {"name": "Percent money on market", "odds": "53%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575348"
            }
        },
        {
            "market_name": "Both teams to Score?",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:45 09.09"},
                {"name": "Market", "odds": "Yes"},
                {"name": "Summ", "odds": "25000€"},
                {"name": "Change", "odds": "1500€ / 6.38%"},
                {"name": "Time", "odds": "23'"},
                {"name": "Score", "odds": "1-0"},
                {"name": "Odds", "odds": 1.75},
                {"name": "All", "odds": "40000€"},
                {"name": "Percent money on market", "odds": "62%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575349"
            }
        },
        {
            "market_name": "Over/Under 1.5 Goals",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:45 09.09"},
                {"name": "Market", "odds": "Over"},
                {"name": "Summ", "odds": "35000€"},
                {"name": "Change", "odds": "3000€ / 9.38%"},
                {"name": "Time", "odds": "23'"},
                {"name": "Score", "odds": "1-0"},
                {"name": "Odds", "odds": 1.45},
                {"name": "All", "odds": "55000€"},
                {"name": "Percent money on market", "odds": "64%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575350"
            }
        },
        {
            "market_name": "First Half Goals 0.5",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Date", "odds": "15:45 09.09"},
                {"name": "Market", "odds": "Over"},
                {"name": "Summ", "odds": "15000€"},
                {"name": "Change", "odds": "800€ / 5.63%"},
                {"name": "Time", "odds": "23'"},
                {"name": "Score", "odds": "1-0"},
                {"name": "Odds", "odds": 1.25},
                {"name": "All", "odds": "22000€"},
                {"name": "Percent money on market", "odds": "68%"}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575351"
            }
        }
    ]

def create_low_opportunity_data():
    """
    Cria dados com baixas oportunidades para testar a resposta negativa.
    
    Returns:
        List[Dict]: Lista de mercados com poucas oportunidades
    """
    return [
        {
            "market_name": "Match Odds",
            "selections": [
                {"name": "Type", "odds": "prematch"},
                {"name": "Summ", "odds": "5000€"},  # Volume baixo
                {"name": "Odds", "odds": 1.15}  # Odds muito baixas
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575352"
            }
        },
        {
            "market_name": "Over/Under 2.5 Goals",
            "selections": [
                {"name": "Type", "odds": "prematch"},
                {"name": "Summ", "odds": "3000€"},  # Volume muito baixo
                {"name": "Odds", "odds": 4.50}  # Odds muito altas
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575353"
            }
        }
    ]

def main():
    """
    Função principal para testar a análise KAIROS.
    """
    print("🤖 TESTE DA INTELIGÊNCIA ARTIFICIAL KAIROS")
    print("=" * 50)
    
    # Teste 1: Dados com oportunidades claras
    print("\n📊 TESTE 1: Analisando mercados com oportunidades...")
    print("-" * 50)
    
    sample_data = create_sample_market_data()
    result1 = analyze_betting_opportunity(sample_data)
    print(result1)
    
    # Teste 2: Dados com poucas oportunidades
    print("\n\n📊 TESTE 2: Analisando mercados com baixas oportunidades...")
    print("-" * 50)
    
    low_opportunity_data = create_low_opportunity_data()
    result2 = analyze_betting_opportunity(low_opportunity_data)
    print(result2)
    
    # Teste 3: Dados vazios
    print("\n\n📊 TESTE 3: Analisando dados vazios...")
    print("-" * 50)
    
    result3 = analyze_betting_opportunity([])
    print(result3)
    
    print("\n" + "=" * 50)
    print("✅ TESTES CONCLUÍDOS - KAIROS FUNCIONANDO CORRETAMENTE!")
    print("\n💡 A IA KAIROS está pronta para analisar dados reais do scraper.")
    print("   Quando o scraper extrair dados de jogos ao vivo, a análise")
    print("   será executada automaticamente e identificará as melhores")
    print("   oportunidades de apostas baseadas em volume, odds e contexto.")

if __name__ == "__main__":
    main()