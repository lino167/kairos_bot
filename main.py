#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Sistema Principal
Sistema de análise de oportunidades de apostas esportivas
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from modules.extractor import GameExtractor
from modules.investigator import GameInvestigator
from modules.game_analyzer import GameAnalyzer, analyze_single_game
from utils.logger import get_logger
from config.settings import MESSAGES

logger = get_logger(__name__)

async def run_basic_extraction():
    """Executa extração básica de dados"""
    logger.info("🚀 Iniciando extração básica de dados...")
    extractor = GameExtractor()
    await extractor.run_extraction(analyze_individual_games=False)

async def run_full_analysis():
    """Executa extração completa com análise individual"""
    logger.info("🚀 Iniciando extração completa com análise individual...")
    extractor = GameExtractor()
    await extractor.run_extraction(analyze_individual_games=True)

async def run_single_game_analysis(game_url):
    """Analisa um único jogo específico"""
    logger.info(f"🎯 Analisando jogo específico: {game_url}")
    result = await analyze_single_game(game_url)
    
    if result:
        print(f"\n✅ Análise concluída para: {result.get('teams', 'N/A')}")
        print(f"📊 Tabelas encontradas: {len(result.get('betting_tables', {}))}")
        print(f"📈 Dados de movimento: {len(result.get('movement_history', []))} entradas")
        print(f"🎯 Score de completude: {result.get('analysis_metrics', {}).get('data_completeness_score', 0):.1%}")
    else:
        print("❌ Falha na análise do jogo")

async def run_investigation():
    """Executa investigação de dados"""
    logger.info("🔍 Iniciando investigação de dados...")
    investigator = GameInvestigator()
    await investigator.run_investigation()

async def main():
    """
    Função principal do sistema
    """
    parser = argparse.ArgumentParser(
        description='Kairos Bot - Sistema de análise de apostas esportivas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                                    # Extração básica
  python main.py --full                            # Extração com análise individual
  python main.py --analyze-game URL               # Analisa jogo específico
  python main.py --investigate                     # Apenas investigação
  python main.py --example                         # Analisa jogo de exemplo
        """
    )
    
    parser.add_argument(
        '--full', 
        action='store_true',
        help='Executa extração completa com análise individual de jogos'
    )
    
    parser.add_argument(
        '--analyze-game',
        type=str,
        metavar='URL',
        help='Analisa um jogo específico pela URL'
    )
    
    parser.add_argument(
        '--investigate',
        action='store_true',
        help='Executa apenas a investigação de dados'
    )
    
    parser.add_argument(
        '--example',
        action='store_true',
        help='Analisa o jogo de exemplo (Millwall U21 - Huddersfield Town U21)'
    )
    
    args = parser.parse_args()
    
    logger.info(MESSAGES['start'])
    
    try:
        if args.example:
            # Analisa o jogo de exemplo fornecido
            example_url = "https://www.excapper.com/?action=game&id=34705909"
            await run_single_game_analysis(example_url)
            
        elif args.analyze_game:
            # Analisa jogo específico
            await run_single_game_analysis(args.analyze_game)
            
        elif args.investigate:
            # Apenas investigação
            await run_investigation()
            
        elif args.full:
            # Extração completa com análise individual
            await run_full_analysis()
            
        else:
            # Extração básica (padrão)
            await run_basic_extraction()
        
        logger.info(MESSAGES['success'].format(message="Operação concluída com sucesso"))
        
    except KeyboardInterrupt:
        logger.info("⏹️ Sistema interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro no sistema: {e}")
        raise

if __name__ == "__main__":
    # Verifica versão do Python
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ é necessário")
        sys.exit(1)
    
    # Executa função principal
    asyncio.run(main())