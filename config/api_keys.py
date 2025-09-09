#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração de Chaves de API

Este arquivo contém as chaves de API necessárias para o funcionamento
do sistema KAIROS. Mantenha este arquivo seguro e não o compartilhe.
"""

import os
from typing import Optional

# Chave da API do Google Gemini
GEMINI_API_KEY = "AIzaSyDI6BLfsi1Txpbx03Cw_0PPLdWpU234D7c"

# Função para obter a chave da API do Gemini
def get_gemini_api_key() -> Optional[str]:
    """
    Retorna a chave da API do Gemini.
    
    Primeiro tenta obter da variável de ambiente GEMINI_API_KEY,
    se não encontrar, usa a chave configurada neste arquivo.
    
    Returns:
        str: Chave da API do Gemini ou None se não encontrada
    """
    # Tentar obter da variável de ambiente primeiro (mais seguro)
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key:
        return api_key
    
    # Se não encontrar na variável de ambiente, usar a chave configurada
    return GEMINI_API_KEY

# Validar se a chave está disponível
def validate_gemini_key() -> bool:
    """
    Valida se a chave da API do Gemini está disponível e válida.
    
    Returns:
        bool: True se a chave está disponível, False caso contrário
    """
    key = get_gemini_api_key()
    return key is not None and len(key) > 20  # Chaves do Google têm mais de 20 caracteres

# Configurações adicionais para integração com Gemini
GEMINI_CONFIG = {
    'model': 'gemini-1.5-flash',  # Modelo mais recente disponível
    'temperature': 0.7,
    'max_tokens': 2048,
    'timeout': 30
}

if __name__ == "__main__":
    # Teste da configuração
    print("🔑 Testando configuração da API do Gemini...")
    
    if validate_gemini_key():
        key = get_gemini_api_key()
        masked_key = key[:8] + "*" * (len(key) - 12) + key[-4:]
        print(f"✅ Chave da API encontrada: {masked_key}")
        print(f"📊 Configuração: {GEMINI_CONFIG}")
    else:
        print("❌ Chave da API não encontrada ou inválida")
        print("💡 Verifique se a chave está configurada corretamente")