#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Envio de Mensagens Telegram
Sistema de notificações para o KAIROS BOT

Autor: KAIROS Team
Versão: 1.0
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from telegram import Bot
    from telegram.error import TelegramError, NetworkError, RetryAfter
except ImportError:
    print("❌ Biblioteca python-telegram-bot não encontrada. Execute: pip install python-telegram-bot")
    raise

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Biblioteca python-dotenv não encontrada. Execute: pip install python-dotenv")
    raise

# Configurar logging
logger = logging.getLogger(__name__)

def escape_markdown(text: str) -> str:
    """
    Escapa caracteres especiais para MarkdownV2 do Telegram.
    
    Args:
        text: Texto a ser escapado
        
    Returns:
        str: Texto com caracteres especiais escapados
    """
    if not text or not isinstance(text, str):
        return str(text) if text is not None else "N/A"
    
    # Caracteres que precisam ser escapados no MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text

class TelegramSender:
    """
    Classe para envio de mensagens via Telegram Bot
    """
    
    def __init__(self, bot_token: str = None, channel_id: str = None):
        """
        Inicializa o sender do Telegram
        
        Args:
            bot_token: Token do bot Telegram
            channel_id: ID do canal/chat de destino
        """
        self.bot_token = bot_token or self._load_from_env('TELEGRAM_BOT_TOKEN')
        self.channel_id = channel_id or self._load_from_env('TELEGRAM_CHANNEL_ID')
        
        if not self.bot_token or not self.channel_id:
            raise ValueError("Token do bot e ID do canal são obrigatórios")
        
        self.bot = Bot(token=self.bot_token)
        self.max_retries = 3
        self.retry_delay = 2
    
    def _load_from_env(self, key: str) -> Optional[str]:
        """Carrega variável de ambiente"""
        # Primeiro tenta carregar do .env
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                env_key, env_value = line.strip().split('=', 1)
                                if env_key == key:
                                    return env_value.strip('"\'')
            except Exception as e:
                logger.warning(f"Erro ao ler .env: {e}")
        
        # Fallback para variável de ambiente do sistema
        return os.getenv(key)
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão com o Telegram
        
        Returns:
            bool: True se a conexão foi bem-sucedida
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Conectado ao bot: {bot_info.first_name} (@{bot_info.username})")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na conexão com Telegram: {e}")
            return False
    
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Envia uma mensagem para o canal
        
        Args:
            message: Texto da mensagem
            parse_mode: Modo de formatação (HTML ou Markdown)
        
        Returns:
            bool: True se enviado com sucesso
        """
        for attempt in range(self.max_retries):
            try:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode=parse_mode
                )
                logger.info("✅ Mensagem enviada com sucesso")
                return True
                
            except RetryAfter as e:
                wait_time = e.retry_after
                logger.warning(f"⏳ Rate limit atingido. Aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except NetworkError as e:
                logger.warning(f"🌐 Erro de rede (tentativa {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                
            except TelegramError as e:
                logger.error(f"❌ Erro do Telegram: {e}")
                return False
                
            except Exception as e:
                logger.error(f"❌ Erro inesperado: {e}")
                return False
        
        logger.error("❌ Falha ao enviar mensagem após todas as tentativas")
        return False
    
    async def send_opportunity_alert(self, game_info: Dict[str, Any], opportunity: Dict[str, Any]) -> bool:
        """
        Envia alerta de oportunidade de aposta
        
        Args:
            game_info: Informações do jogo
            opportunity: Dados da oportunidade
        
        Returns:
            bool: True se enviado com sucesso
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""🚨 <b>OPORTUNIDADE DETECTADA</b>

🏆 <b>{game_info.get('teams', 'N/A')}</b>
🏟️ Liga: {game_info.get('league', 'N/A')}
📊 Mercado: {opportunity.get('market_name', 'N/A')}
🎯 Seleção: {opportunity.get('selection', 'N/A')}
💰 Odds: {opportunity.get('odds', 'N/A')}
🤖 Confiança IA: {opportunity.get('ai_confidence', 0)}%
⏰ {timestamp}

🔗 <a href="{game_info.get('url', '#')}">Ver Jogo</a>"""
        
        return await self.send_message(message)

    async def send_telegram_alert(self, analysis_result: dict) -> bool:
        """
        Envia alerta formatado para o canal do Telegram usando MarkdownV2.
        
        Args:
            analysis_result: Dicionário com resultado da análise da IA Gemini
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Obter dados da partida
            dados_partida = analysis_result.get('dados_partida', {})
            teams = escape_markdown(dados_partida.get('teams', 'Times não disponíveis'))
            
            # Obter link da Betfair do primeiro mercado
            dados_mercados = analysis_result.get('dados_mercados', [{}])
            betfair_link = 'Link não disponível'
            if dados_mercados and len(dados_mercados) > 0:
                links = dados_mercados[0].get('links', {})
                betfair_link = links.get('betfair_url', 'Link não disponível')
            
            # Escapar dados da análise
            justificativa = escape_markdown(analysis_result.get('Justificativa da Análise', 'Análise não disponível'))
            mercado_sugerido = escape_markdown(analysis_result.get('Mercado Sugerido', 'Não especificado'))
            selecao = escape_markdown(analysis_result.get('Seleção', 'Não especificada'))
            confianca = escape_markdown(str(analysis_result.get('Nível de Confiança', 'N/A')))
            
            # Formatar mensagem com MarkdownV2
            message = f"""🚨 *Alerta KAIROS \\- Oportunidade Detectada* 🚨

*{teams}*

*Análise da IA:*

*{justificativa}*

\\-\\-\\-

*Mercado Sugerido:*
*{mercado_sugerido}*

*Seleção:*
*{selecao}*

*Nível de Confiança:*
*{confianca}*

\\-\\-\\-

[Acessar Mercado na Betfair]({betfair_link})"""
            
            # Tentar enviar com MarkdownV2
            try:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode='MarkdownV2',
                    disable_web_page_preview=False
                )
                logger.info("✅ Alerta enviado com sucesso para o Telegram!")
                return True
                
            except TelegramError as e:
                logger.warning(f"⚠️ Erro com MarkdownV2, tentando formato simples: {e}")
                # Tentar enviar versão simplificada sem formatação
                simple_message = f"""🚨 ALERTA KAIROS - Oportunidade Detectada 🚨

{dados_partida.get('teams', 'Times não disponíveis')}

Análise: {analysis_result.get('Justificativa da Análise', 'N/A')}

Mercado: {analysis_result.get('Mercado Sugerido', 'N/A')}
Seleção: {analysis_result.get('Seleção', 'N/A')}
Confiança: {analysis_result.get('Nível de Confiança', 'N/A')}

Link: {betfair_link}"""
                
                return await self.send_message(simple_message, parse_mode=None)
                
        except Exception as e:
            logger.error(f"❌ Erro geral no envio do alerta: {e}")
            return False
    
    async def send_analysis_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Envia resumo da análise
        
        Args:
            summary: Dados do resumo
        
        Returns:
            bool: True se enviado com sucesso
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_emoji = "✅" if summary.get('games_with_opportunities', 0) > 0 else "📊"
        
        message = f"""📈 <b>RESUMO DA ANÁLISE</b>

🎮 Total de jogos: {summary.get('total_games', 0)}
🎯 Oportunidades: {summary.get('games_with_opportunities', 0)}
⏰ Análise: {timestamp}

{status_emoji} Status: Análise concluída"""
        
        return await self.send_message(message)
    
    async def send_error_alert(self, error_message: str) -> bool:
        """
        Envia alerta de erro
        
        Args:
            error_message: Mensagem de erro
        
        Returns:
            bool: True se enviado com sucesso
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""🚨 <b>ERRO NO SISTEMA</b>

❌ {error_message}
⏰ {timestamp}

🔧 Verificar logs para mais detalhes"""
        
        return await self.send_message(message)
    
    async def send_system_start(self) -> bool:
        """
        Envia notificação de início do sistema
        
        Returns:
            bool: True se enviado com sucesso
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""🤖 <b>KAIROS BOT INICIADO</b>

✅ Sistema online
📱 Telegram conectado
🧠 IA configurada
⏰ {timestamp}"""
        
        return await self.send_message(message)

# Função principal solicitada usando dotenv
async def send_telegram_alert(analysis_result: dict):
    """
    Envia alerta formatado para o canal do Telegram.
    Função standalone que carrega configurações do .env
    
    Args:
        analysis_result: Dicionário com resultado da análise da IA Gemini
    """
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
        
        if not BOT_TOKEN or not CHANNEL_ID:
            print("❌ Erro: Token do bot ou ID do canal não configurados nas variáveis de ambiente")
            return False
        
        # Usar a classe TelegramSender
        sender = TelegramSender(BOT_TOKEN, CHANNEL_ID)
        return await sender.send_telegram_alert(analysis_result)
        
    except Exception as e:
        print(f"❌ Erro geral no envio do alerta: {e}")
        return False

# Funções de conveniência
async def send_telegram_message(message: str, bot_token: str = None, channel_id: str = None) -> bool:
    """
    Função de conveniência para envio rápido de mensagem
    
    Args:
        message: Texto da mensagem
        bot_token: Token do bot (opcional)
        channel_id: ID do canal (opcional)
    
    Returns:
        bool: True se enviado com sucesso
    """
    try:
        sender = TelegramSender(bot_token, channel_id)
        return await sender.send_message(message)
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {e}")
        return False

async def send_opportunity_notification(game_info: Dict[str, Any], opportunity: Dict[str, Any]) -> bool:
    """
    Função de conveniência para envio de oportunidade
    
    Args:
        game_info: Informações do jogo
        opportunity: Dados da oportunidade
    
    Returns:
        bool: True se enviado com sucesso
    """
    try:
        sender = TelegramSender()
        return await sender.send_opportunity_alert(game_info, opportunity)
    except Exception as e:
        logger.error(f"❌ Erro ao enviar oportunidade: {e}")
        return False

# Exemplo de uso
if __name__ == "__main__":
    # Dados de teste para verificar o funcionamento
    mock_analysis = {
        'dados_partida': {
            'teams': 'Real Madrid vs Barcelona',
            'league': 'La Liga',
            'datetime': '2025-01-15 20:00'
        },
        'dados_mercados': [
            {
                'market_name': 'Match Odds',
                'links': {
                    'betfair_url': 'https://www.betfair.com/exchange/plus/football/market/1.123456789'
                }
            }
        ],
        'Justificativa da Análise': 'Análise detectou discrepância significativa nas odds do mercado Match Odds. O Real Madrid apresenta valor excelente considerando o histórico recente e estatísticas de confronto direto.',
        'Mercado Sugerido': 'Match Odds',
        'Seleção': 'Real Madrid',
        'Nível de Confiança': '85%'
    }
    
    print("🧪 Testando envio de alerta para o Telegram...")
    print("📝 Dados de teste:")
    print(f"   Times: {mock_analysis['dados_partida']['teams']}")
    print(f"   Mercado: {mock_analysis['Mercado Sugerido']}")
    print(f"   Confiança: {mock_analysis['Nível de Confiança']}")
    
    # Executar teste assíncrono
    asyncio.run(send_telegram_alert(mock_analysis))