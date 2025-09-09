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
from scraper.excapper_scraper import run_excapper_analysis
from notifications.telegram_sender import TelegramSender as TelegramNotifier, send_opportunity_notification
from utils.logger import get_logger
from config.settings import MESSAGES
from config.api_keys import get_gemini_api_key, validate_gemini_key
from config.telegram_config import get_telegram_config, validate_telegram_config
import os
from datetime import datetime

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
async def run_kairos_analysis(telegram_config=None):
    """Executa análise completa KAIROS com notificações Telegram"""
    logger.info("🚀 Iniciando análise KAIROS completa...")
    
    # Configurar notificador Telegram se fornecido
    telegram_notifier = None
    if telegram_config:
        telegram_notifier = TelegramNotifier(
            bot_token=telegram_config.get('bot_token'),
            channel_id=telegram_config.get('chat_id')
        )
        
        # Teste de conexão
        if await telegram_notifier.test_connection():
            logger.info("✅ Telegram conectado com sucesso")
        else:
            logger.warning("⚠️ Falha na conexão com Telegram")
    
    try:
        # Executar scraper principal
        results = await run_excapper_analysis()
        
        # Processar resultados e enviar notificações
        if results and telegram_notifier:
            await process_results_and_notify(results, telegram_notifier)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erro na análise KAIROS: {e}")
        if telegram_notifier:
            error_msg = f"🚨 <b>ERRO KAIROS</b>\n\n❌ {str(e)}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            await telegram_notifier.send_message(error_msg)
        raise
    finally:
        if telegram_notifier:
            logger.info("🔌 Finalizando conexão Telegram")

async def process_results_and_notify(results, telegram_notifier):
    """Processa resultados e envia notificações"""
    if not results or not telegram_notifier:
        return
    
    # Se results é uma lista de jogos, processar adequadamente
    if isinstance(results, list):
        processed_games = results
        total_games = len(results)
        games_with_opportunities = sum(1 for game in results if game.get('has_prediction') and game.get('ai_confidence', 0) > 60)
    else:
        # Se results é um dicionário (formato antigo)
        processed_games = results.get('processed_games', [])
        total_games = results.get('total_games', 0)
        games_with_opportunities = results.get('games_with_opportunities', 0)
    
    # Enviar resumo da análise
    summary = {
        'total_games': total_games,
        'games_with_opportunities': games_with_opportunities,
        'timestamp': datetime.now().isoformat()
    }
    
    await telegram_notifier.send_analysis_summary(summary)
    
    # Enviar alertas de oportunidades individuais
    for game in processed_games:
        if game.get('has_prediction') and game.get('ai_confidence', 0) > 60:
            game_info = {
                'teams': game.get('teams', 'N/A'),
                'league': game.get('league', 'N/A')
            }
            
            opportunity = {
                'market_name': 'Análise KAIROS',
                'selection': 'Oportunidade Detectada',
                'odds': 'N/A',
                'ai_confidence': game.get('ai_confidence', 0)
            }
            
            await telegram_notifier.send_opportunity_alert(game_info, opportunity)
            await asyncio.sleep(1)  # Evitar spam

async def run_continuous_monitoring(telegram_config=None, interval_minutes=30):
    """Executa monitoramento contínuo com intervalo configurável"""
    logger.info(f"🔄 Iniciando monitoramento contínuo (intervalo: {interval_minutes} min)")
    
    while True:
        try:
            await run_kairos_analysis(telegram_config)
            logger.info(f"⏰ Próxima análise em {interval_minutes} minutos")
            await asyncio.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("🛑 Monitoramento interrompido pelo usuário")
            break
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento: {e}")
            await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente

def load_telegram_config():
    """Carrega configuração do Telegram"""
    try:
        # Primeiro tenta carregar das configurações do arquivo
        if validate_telegram_config():
            return get_telegram_config()
        
        # Fallback para variáveis de ambiente
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            return {
                'bot_token': bot_token,
                'chat_id': chat_id
            }
    except Exception as e:
        logger.warning(f"Erro ao carregar configuração Telegram: {e}")
    
    return None

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='KAIROS BOT - Sistema de Análise de Apostas')
    parser.add_argument('--mode', choices=['single', 'continuous'], 
                       default='single', help='Modo de operação')
    parser.add_argument('--interval', type=int, default=30,
                       help='Intervalo em minutos para modo contínuo (padrão: 30)')
    parser.add_argument('--telegram', action='store_true',
                       help='Habilitar notificações Telegram')
    parser.add_argument('--bot-token', help='Token do bot Telegram')
    parser.add_argument('--chat-id', help='ID do chat Telegram')
    
    args = parser.parse_args()
    
    # Configurar Telegram
    telegram_config = None
    if args.telegram:
        if args.bot_token and args.chat_id:
            telegram_config = {
                'bot_token': args.bot_token,
                'chat_id': args.chat_id
            }
        else:
            telegram_config = load_telegram_config()
            
        if not telegram_config:
            logger.warning("⚠️ Configuração Telegram não encontrada. Executando sem notificações.")
        else:
            logger.info("✅ Configuração Telegram carregada com sucesso")
    
    # Verificar Gemini AI
    if not validate_gemini_key():
        logger.warning("⚠️ Chave Gemini AI não configurada. Algumas funcionalidades podem estar limitadas.")
    
    try:
        print("\n" + "="*60)
        print("🤖 KAIROS BOT - Sistema Inteligente de Análise")
        print("="*60)
        print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔧 Modo: {args.mode.upper()}")
        print(f"📱 Telegram: {'✅ Ativo' if telegram_config else '❌ Inativo'}")
        print(f"🧠 Gemini AI: {'✅ Ativo' if validate_gemini_key() else '❌ Inativo'}")
        print("="*60 + "\n")
        
        if args.mode == 'single':
            await run_kairos_analysis(telegram_config)
        elif args.mode == 'continuous':
            await run_continuous_monitoring(telegram_config, args.interval)
        
        logger.info("✅ Execução concluída com sucesso")
        
    except KeyboardInterrupt:
        logger.info("🛑 Execução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
        raise

if __name__ == "__main__":
    # Verifica versão do Python
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ é necessário")
        sys.exit(1)
    
    # Executa função principal
    asyncio.run(main())