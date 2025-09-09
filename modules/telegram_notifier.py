#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Notifier - Módulo para envio de mensagens no Telegram

Este módulo fornece funcionalidades para:
1. Envio de mensagens de texto
2. Envio de mensagens formatadas (HTML/Markdown)
3. Envio de alertas de oportunidades
4. Configuração de canais/grupos
5. Tratamento de erros e retry automático

Autor: KAIROS Team
Versão: 1.0
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import quote

class TelegramNotifier:
    """
    Classe para envio de notificações via Telegram Bot API.
    """
    
    def __init__(self, bot_token: str, default_chat_id: Optional[str] = None):
        """
        Inicializa o notificador do Telegram.
        
        Args:
            bot_token (str): Token do bot do Telegram
            default_chat_id (str, optional): ID do chat padrão
        """
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()
    
    async def send_message(
        self, 
        message: str, 
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem para o Telegram.
        
        Args:
            message (str): Texto da mensagem
            chat_id (str, optional): ID do chat (usa o padrão se não especificado)
            parse_mode (str): Modo de formatação (HTML, Markdown, None)
            disable_web_page_preview (bool): Desabilita preview de links
            retry_count (int): Número de tentativas em caso de erro
            
        Returns:
            Dict[str, Any]: Resposta da API do Telegram
        """
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            raise ValueError("Chat ID não especificado e nenhum padrão configurado")
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        for attempt in range(retry_count):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession()
                
                async with self.session.post(url, json=payload) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("ok"):
                        return result
                    else:
                        error_msg = result.get("description", "Erro desconhecido")
                        if attempt == retry_count - 1:
                            raise Exception(f"Erro na API do Telegram: {error_msg}")
                        await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                        
            except Exception as e:
                if attempt == retry_count - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Falha ao enviar mensagem após todas as tentativas")
    
    async def send_opportunity_alert(
        self, 
        game_info: Dict[str, Any], 
        opportunity: Dict[str, Any],
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia um alerta formatado de oportunidade de aposta.
        
        Args:
            game_info (Dict): Informações do jogo
            opportunity (Dict): Dados da oportunidade
            chat_id (str, optional): ID do chat
            
        Returns:
            Dict[str, Any]: Resposta da API do Telegram
        """
        # Formatação da mensagem de oportunidade
        message = self._format_opportunity_message(game_info, opportunity)
        return await self.send_message(message, chat_id)
    
    async def send_analysis_summary(
        self, 
        summary: Dict[str, Any],
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia um resumo de análise formatado.
        
        Args:
            summary (Dict): Dados do resumo
            chat_id (str, optional): ID do chat
            
        Returns:
            Dict[str, Any]: Resposta da API do Telegram
        """
        message = self._format_analysis_summary(summary)
        return await self.send_message(message, chat_id)
    
    def _format_opportunity_message(self, game_info: Dict[str, Any], opportunity: Dict[str, Any]) -> str:
        """
        Formata uma mensagem de oportunidade para o Telegram.
        
        Args:
            game_info (Dict): Informações do jogo
            opportunity (Dict): Dados da oportunidade
            
        Returns:
            str: Mensagem formatada em HTML
        """
        teams = game_info.get('teams', 'N/A')
        league = game_info.get('league', 'N/A')
        confidence = opportunity.get('ai_confidence', 0)
        market = opportunity.get('market_name', 'N/A')
        selection = opportunity.get('selection', 'N/A')
        odds = opportunity.get('odds', 'N/A')
        
        # Emoji baseado na confiança
        confidence_emoji = "🔥" if confidence >= 80 else "⚡" if confidence >= 60 else "💡"
        
        message = f"""
{confidence_emoji} <b>OPORTUNIDADE DETECTADA</b> {confidence_emoji}

🏆 <b>Jogo:</b> {teams}
🏅 <b>Liga:</b> {league}
📊 <b>Mercado:</b> {market}
🎯 <b>Seleção:</b> {selection}
💰 <b>Odds:</b> {odds}
🧠 <b>Confiança IA:</b> {confidence}%

⏰ <b>Detectado em:</b> {datetime.now().strftime('%H:%M:%S')}

#KAIROS #Oportunidade #Apostas
        """.strip()
        
        return message
    
    def _format_analysis_summary(self, summary: Dict[str, Any]) -> str:
        """
        Formata um resumo de análise para o Telegram.
        
        Args:
            summary (Dict): Dados do resumo
            
        Returns:
            str: Mensagem formatada em HTML
        """
        total_games = summary.get('total_games', 0)
        opportunities = summary.get('games_with_opportunities', 0)
        timestamp = summary.get('timestamp', datetime.now().isoformat())
        
        message = f"""
📊 <b>RELATÓRIO DE ANÁLISE</b>

🎮 <b>Jogos Analisados:</b> {total_games}
🎯 <b>Oportunidades:</b> {opportunities}
📈 <b>Taxa de Sucesso:</b> {(opportunities/total_games*100) if total_games > 0 else 0:.1f}%

⏰ <b>Análise concluída em:</b> {datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')}

#KAIROS #Relatório #Análise
        """.strip()
        
        return message
    
    async def test_connection(self, chat_id: Optional[str] = None) -> bool:
        """
        Testa a conexão com o Telegram enviando uma mensagem de teste.
        
        Args:
            chat_id (str, optional): ID do chat para teste
            
        Returns:
            bool: True se o teste foi bem-sucedido
        """
        try:
            test_message = f"🤖 <b>KAIROS BOT</b>\n\n✅ Conexão testada com sucesso!\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            result = await self.send_message(test_message, chat_id)
            return result.get("ok", False)
        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
            return False
    
    async def get_chat_info(self, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém informações sobre um chat.
        
        Args:
            chat_id (str, optional): ID do chat
            
        Returns:
            Dict[str, Any]: Informações do chat
        """
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            raise ValueError("Chat ID não especificado")
        
        url = f"{self.base_url}/getChat"
        payload = {"chat_id": target_chat_id}
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(url, json=payload) as response:
            result = await response.json()
            
            if response.status == 200 and result.get("ok"):
                return result.get("result", {})
            else:
                error_msg = result.get("description", "Erro desconhecido")
                raise Exception(f"Erro ao obter informações do chat: {error_msg}")


# Funções de conveniência para uso direto
async def send_telegram_message(
    bot_token: str, 
    chat_id: str, 
    message: str, 
    parse_mode: str = "HTML"
) -> Dict[str, Any]:
    """
    Função de conveniência para envio rápido de mensagem.
    
    Args:
        bot_token (str): Token do bot
        chat_id (str): ID do chat
        message (str): Mensagem a ser enviada
        parse_mode (str): Modo de formatação
        
    Returns:
        Dict[str, Any]: Resposta da API
    """
    async with TelegramNotifier(bot_token, chat_id) as notifier:
        return await notifier.send_message(message, parse_mode=parse_mode)


async def send_opportunity_notification(
    bot_token: str,
    chat_id: str,
    game_info: Dict[str, Any],
    opportunity: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Função de conveniência para envio de alerta de oportunidade.
    
    Args:
        bot_token (str): Token do bot
        chat_id (str): ID do chat
        game_info (Dict): Informações do jogo
        opportunity (Dict): Dados da oportunidade
        
    Returns:
        Dict[str, Any]: Resposta da API
    """
    async with TelegramNotifier(bot_token, chat_id) as notifier:
        return await notifier.send_opportunity_alert(game_info, opportunity)


# Exemplo de uso
if __name__ == "__main__":
    async def test_telegram():
        # Configurações de teste (substitua pelos seus valores)
        BOT_TOKEN = "SEU_BOT_TOKEN_AQUI"
        CHAT_ID = "SEU_CHAT_ID_AQUI"
        
        async with TelegramNotifier(BOT_TOKEN, CHAT_ID) as notifier:
            # Teste de conexão
            success = await notifier.test_connection()
            print(f"Teste de conexão: {'✅ Sucesso' if success else '❌ Falha'}")
            
            # Exemplo de oportunidade
            game_info = {
                "teams": "Barcelona vs Real Madrid",
                "league": "La Liga"
            }
            
            opportunity = {
                "market_name": "Match Odds",
                "selection": "Barcelona",
                "odds": "2.50",
                "ai_confidence": 85
            }
            
            # Enviar alerta de oportunidade
            await notifier.send_opportunity_alert(game_info, opportunity)
    
    # Executar teste
    # asyncio.run(test_telegram())
    print("Módulo Telegram Notifier carregado com sucesso!")