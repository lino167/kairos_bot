#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração do Telegram Bot
Credenciais e configurações para notificações
"""

import os

# Configurações de mensagens
MESSAGE_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,
    "timeout": 30,
    "parse_mode": "HTML"
}

# Templates de mensagens
MESSAGE_TEMPLATES = {
    "opportunity_alert": "🚨 <b>OPORTUNIDADE DETECTADA</b>\n\n🏆 <b>{teams}</b>\n🏟️ Liga: {league}\n📊 Mercado: {market_name}\n🎯 Seleção: {selection}\n💰 Odds: {odds}\n🤖 Confiança IA: {ai_confidence}%\n⏰ {timestamp}",
    
    "analysis_summary": "📈 <b>RESUMO DA ANÁLISE</b>\n\n🎮 Total de jogos: {total_games}\n🎯 Oportunidades: {games_with_opportunities}\n⏰ Análise: {timestamp}\n\n{status_emoji} Status: Análise concluída",
    
    "error_alert": "🚨 <b>ERRO NO SISTEMA</b>\n\n❌ {error_message}\n⏰ {timestamp}\n\n🔧 Verificar logs para mais detalhes",
    
    "system_start": "🤖 <b>KAIROS BOT INICIADO</b>\n\n✅ Sistema online\n📱 Telegram conectado\n🧠 IA configurada\n⏰ {timestamp}"
}

def get_telegram_config():
    """
    Retorna configuração do Telegram carregada das variáveis de ambiente.
    
    Returns:
        dict: Configuração completa do Telegram
        
    Raises:
        ValueError: Se as variáveis de ambiente não estiverem configuradas
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        raise ValueError(
            "Token do bot Telegram não encontrado. "
            "Configure a variável de ambiente TELEGRAM_BOT_TOKEN."
        )
    
    if not chat_id:
        raise ValueError(
            "Chat ID do Telegram não encontrado. "
            "Configure a variável de ambiente TELEGRAM_CHAT_ID."
        )
    
    return {
        'bot_token': bot_token,
        'chat_id': chat_id,
        'message_config': MESSAGE_CONFIG,
        'templates': MESSAGE_TEMPLATES
    }