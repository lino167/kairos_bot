#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Configurações Centralizadas
Todas as configurações do sistema em um local centralizado
"""

import os
from pathlib import Path

# Diretórios do projeto
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
MODULES_DIR = PROJECT_ROOT / "modules"
UTILS_DIR = PROJECT_ROOT / "utils"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# URLs e configurações do site
BASE_URL = "https://www.excapper.com/"
GAME_URL_TEMPLATE = "https://www.excapper.com/?action=game&id={game_id}"

# Configurações do Playwright
PLAYWRIGHT_CONFIG = {
    'headless': True,
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'timeout': 30000,
    'wait_until': 'networkidle',
    'args': ['--no-sandbox', '--disable-dev-shm-usage']
}

# Configurações de timeouts
TIMEOUTS = {
    'page_load': 30000,
    'element_wait': 10000,
    'network_idle': 5000,
    'screenshot': 5000
}

# Configurações principais do sistema
MAIN_CONFIG = {
    'version': '2.0.0',
    'author': 'KAIROS BOT Team',
    'headless_mode': True,
    'default_timeout': 30,
    'max_games_per_run': 200,
    'enable_screenshots': True,
    'enable_logging': True
}

# Seletores CSS
SELECTORS = {
    'game_rows': 'tr.a_link',
    'tables': 'table',
    'game_cells': 'td',
    'country_img': 'img',
    'navigation_tabs': '.tab, .nav-tab'
}

# Configurações de extração
EXTRACTION_CONFIG = {
    'max_games_per_run': 200,
    'validate_links_sample': 3,
    'retry_attempts': 3,
    'delay_between_requests': 1,
    'save_screenshots': True,
    'save_html': True
}

# Configurações de arquivos
FILE_CONFIG = {
    'encoding': 'utf-8',
    'json_indent': 2,
    'ensure_ascii': False,
    'timestamp_format': '%Y%m%d_%H%M%S',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# Padrões de nomes de arquivos
FILE_PATTERNS = {
    'games_data': 'games_data_{timestamp}.json',
    'investigation_report': 'investigation_report_{timestamp}.json',
    'comparison_report': 'comparison_report_{timestamp}.json',
    'screenshot_full': 'full_page_{timestamp}.png',
    'screenshot_viewport': 'viewport_{timestamp}.png',
    'html_dump': 'page_dump_{timestamp}.html',
    'log_file': 'kairos_bot_{date}.log'
}

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Configurações de dados
DATA_CONFIG = {
    'required_fields': ['game_id', 'teams', 'league', 'date_time', 'game_link'],
    'optional_fields': ['money', 'country', 'home_team', 'away_team'],
    'validation_rules': {
        'game_id': r'^\d+$',
        'money': r'\d+\s*€',
        'date_time': r'\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}'
    }
}

# Configurações de performance
PERFORMANCE_CONFIG = {
    'max_concurrent_requests': 5,
    'request_delay': 0.5,
    'max_retries': 3,
    'backoff_factor': 2,
    'connection_timeout': 30,
    'read_timeout': 60
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    'track_network_calls': True,
    'track_console_logs': True,
    'track_errors': True,
    'save_performance_metrics': True,
    'alert_on_errors': False
}

# Configurações de exportação
EXPORT_CONFIG = {
    'formats': ['json', 'csv', 'excel'],
    'csv_delimiter': ',',
    'excel_sheet_name': 'Jogos_Extraidos',
    'include_metadata': True,
    'compress_output': False
}

# Mensagens do sistema
MESSAGES = {
    'start': "🚀 Iniciando Kairos Bot...",
    'browser_setup': "🌐 Configurando navegador...",
    'navigation': "📍 Navegando para {url}...",
    'extraction_start': "📊 Iniciando extração de dados...",
    'extraction_complete': "✅ Extração concluída: {count} jogos extraídos",
    'validation_start': "🔍 Validando links extraídos...",
    'save_data': "💾 Salvando dados em {filename}...",
    'cleanup': "🧹 Limpando recursos...",
    'error': "❌ Erro: {error}",
    'warning': "⚠️ Aviso: {warning}",
    'success': "✅ Sucesso: {message}"
}

# Função para criar diretórios necessários
def ensure_directories():
    """Cria todos os diretórios necessários se não existirem"""
    directories = [DATA_DIR, LOGS_DIR, SCREENSHOTS_DIR]
    for directory in directories:
        directory.mkdir(exist_ok=True)

# Função para obter configuração por ambiente
def get_config_by_env(env='production'):
    """Retorna configurações específicas por ambiente"""
    configs = {
        'development': {
            'headless': False,
            'timeout': 60000,
            'log_level': 'DEBUG'
        },
        'production': {
            'headless': True,
            'timeout': 30000,
            'log_level': 'INFO'
        },
        'testing': {
            'headless': True,
            'timeout': 15000,
            'log_level': 'WARNING'
        }
    }
    return configs.get(env, configs['production'])

# Validação de configurações
def validate_config():
    """Valida se todas as configurações estão corretas"""
    errors = []
    
    # Verifica se URLs são válidas
    if not BASE_URL.startswith('http'):
        errors.append("BASE_URL deve começar com http ou https")
    
    # Verifica se diretórios podem ser criados
    try:
        ensure_directories()
    except Exception as e:
        errors.append(f"Erro ao criar diretórios: {e}")
    
    return errors

if __name__ == "__main__":
    # Testa as configurações
    errors = validate_config()
    if errors:
        print("❌ Erros de configuração encontrados:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Todas as configurações estão válidas")
        ensure_directories()
        print(f"📁 Diretórios criados: {[str(d) for d in [DATA_DIR, LOGS_DIR, SCREENSHOTS_DIR]]}")