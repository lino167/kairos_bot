#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pacote de Notificações - KAIROS BOT
Módulos para envio de notificações via diferentes canais
"""

from .telegram_sender import (
    TelegramSender,
    send_telegram_message,
    send_opportunity_notification
)

__all__ = [
    'TelegramSender',
    'send_telegram_message', 
    'send_opportunity_notification'
]

__version__ = '1.0.0'
__author__ = 'KAIROS Team'