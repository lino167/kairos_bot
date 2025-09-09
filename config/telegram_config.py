#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração do Telegram Bot
Credenciais e configurações para notificações
"""

# Configurações do Telegram Bot
TELEGRAM_BOT_TOKEN = "5295379026:AAH2AU44kh7cTOtzTxuAVxUuE2WZBT834JA"
TELEGRAM_CHAT_ID = "-1002419962060"

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
    """Retorna configuração do Telegram"""
    return {
        'bot_token': TELEGRAM_BOT_TOKEN,
        'chat_id': TELEGRAM_CHAT_ID,
        'message_config': MESSAGE_CONFIG,
        'templates': MESSAGE_TEMPLATES
    }

def validate_telegram_config():
    """Valida se as configurações estão corretas"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    if not TELEGRAM_BOT_TOKEN.startswith(('1', '2', '5', '6', '7')):
        return False
        
    if not TELEGRAM_CHAT_ID.startswith('-'):
        return False
        
    return True