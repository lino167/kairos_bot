#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Uso do Módulo Telegram Sender
Demonstra como integrar notificações Telegram no KAIROS BOT
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from notifications.telegram_sender import TelegramSender, send_telegram_message, send_opportunity_notification
from utils.logger import get_logger

logger = get_logger(__name__)

async def exemplo_basico():
    """
    Exemplo básico de envio de mensagem
    """
    print("\n🔹 Exemplo 1: Mensagem Básica")
    
    # Método 1: Usando a função de conveniência
    sucesso = await send_telegram_message("🧪 <b>Teste Básico</b>\n\n✅ Mensagem enviada via função de conveniência!")
    
    if sucesso:
        print("✅ Mensagem básica enviada com sucesso")
    else:
        print("❌ Falha ao enviar mensagem básica")

async def exemplo_classe_completa():
    """
    Exemplo usando a classe TelegramSender completa
    """
    print("\n🔹 Exemplo 2: Classe Completa")
    
    try:
        # Criar instância do sender
        sender = TelegramSender()
        
        # Testar conexão
        if await sender.test_connection():
            print("✅ Conexão estabelecida")
            
            # Enviar notificação de início do sistema
            await sender.send_system_start()
            
            # Aguardar um pouco
            await asyncio.sleep(2)
            
            # Enviar resumo de análise
            summary = {
                'total_games': 15,
                'games_with_opportunities': 4
            }
            await sender.send_analysis_summary(summary)
            
            print("✅ Notificações enviadas")
        else:
            print("❌ Falha na conexão")
            
    except Exception as e:
        logger.error(f"Erro no exemplo: {e}")
        print(f"❌ Erro: {e}")

async def exemplo_oportunidade():
    """
    Exemplo de notificação de oportunidade
    """
    print("\n🔹 Exemplo 3: Oportunidade de Aposta")
    
    # Dados de exemplo de um jogo
    game_info = {
        'teams': 'Manchester United vs Liverpool',
        'league': 'Premier League',
        'url': 'https://www.excapper.com/?action=game&id=12345'
    }
    
    # Dados da oportunidade detectada
    opportunity = {
        'market_name': 'Resultado Final',
        'selection': 'Manchester United',
        'odds': '2.85',
        'ai_confidence': 92
    }
    
    # Enviar notificação
    sucesso = await send_opportunity_notification(game_info, opportunity)
    
    if sucesso:
        print("✅ Oportunidade enviada com sucesso")
    else:
        print("❌ Falha ao enviar oportunidade")

async def exemplo_erro():
    """
    Exemplo de notificação de erro
    """
    print("\n🔹 Exemplo 4: Notificação de Erro")
    
    try:
        sender = TelegramSender()
        
        # Simular um erro
        error_message = "Falha na conexão com o site excapper.com - Timeout após 30s"
        
        await sender.send_error_alert(error_message)
        print("✅ Alerta de erro enviado")
        
    except Exception as e:
        print(f"❌ Erro ao enviar alerta: {e}")

async def exemplo_personalizado():
    """
    Exemplo de mensagem personalizada com formatação HTML
    """
    print("\n🔹 Exemplo 5: Mensagem Personalizada")
    
    mensagem_personalizada = """
🎯 <b>ANÁLISE KAIROS CONCLUÍDA</b>

📊 <b>Estatísticas:</b>
• Jogos analisados: 25
• Oportunidades encontradas: 7
• Precisão média: 89.5%
• Tempo de análise: 3m 42s

🏆 <b>Melhores Oportunidades:</b>
1. Barcelona vs Real Madrid - <code>Over 2.5</code> (94% confiança)
2. Chelsea vs Arsenal - <code>BTTS</code> (87% confiança)
3. PSG vs Lyon - <code>PSG Win</code> (91% confiança)

🔗 <a href="https://kairos-bot.com/dashboard">Ver Dashboard Completo</a>

⏰ Próxima análise em 30 minutos
    """
    
    sucesso = await send_telegram_message(mensagem_personalizada)
    
    if sucesso:
        print("✅ Mensagem personalizada enviada")
    else:
        print("❌ Falha ao enviar mensagem personalizada")

async def main():
    """
    Função principal - executa todos os exemplos
    """
    print("🤖 KAIROS BOT - Exemplos de Integração Telegram")
    print("=" * 50)
    
    try:
        # Executar exemplos em sequência
        await exemplo_basico()
        await asyncio.sleep(1)
        
        await exemplo_classe_completa()
        await asyncio.sleep(1)
        
        await exemplo_oportunidade()
        await asyncio.sleep(1)
        
        await exemplo_erro()
        await asyncio.sleep(1)
        
        await exemplo_personalizado()
        
        print("\n" + "=" * 50)
        print("✅ Todos os exemplos executados com sucesso!")
        print("\n💡 Dicas de Integração:")
        print("• Use send_telegram_message() para mensagens simples")
        print("• Use TelegramSender() para controle completo")
        print("• Sempre trate exceções em produção")
        print("• Configure rate limiting para evitar spam")
        print("• Use HTML para formatação rica das mensagens")
        
    except KeyboardInterrupt:
        print("\n🛑 Execução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    # Executar exemplos
    asyncio.run(main())