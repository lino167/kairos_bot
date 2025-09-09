#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração de Chaves de API

Este arquivo contém as chaves de API necessárias para o funcionamento
do sistema KAIROS. Mantenha este arquivo seguro e não o compartilhe.
"""

import os

# Função para obter a chave da API do Gemini
def get_gemini_api_key() -> str:
    """
    Retorna a chave da API do Gemini a partir da variável de ambiente.
    
    Returns:
        str: Chave da API do Gemini
        
    Raises:
        ValueError: Se a variável de ambiente GEMINI_API_KEY não estiver configurada
    """
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "Chave da API do Gemini não encontrada. "
            "Configure a variável de ambiente GEMINI_API_KEY."
        )
    
    return api_key

# Validar se a chave está disponível
def validate_gemini_key() -> bool:
    """
    Valida se a chave da API do Gemini está disponível e válida.
    
    Returns:
        bool: True se a chave está disponível, False caso contrário
    """
    try:
        key = get_gemini_api_key()
        return len(key) > 20  # Chaves do Google têm mais de 20 caracteres
    except ValueError:
        return False

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
        try:
            key = get_gemini_api_key()
            masked_key = key[:8] + "*" * (len(key) - 12) + key[-4:]
            print(f"✅ Chave da API encontrada: {masked_key}")
            print(f"📊 Configuração: {GEMINI_CONFIG}")
        except ValueError as e:
            print(f"❌ Erro: {e}")
    else:
        print("❌ Chave da API não encontrada ou inválida")
        print("💡 Configure a variável de ambiente GEMINI_API_KEY")