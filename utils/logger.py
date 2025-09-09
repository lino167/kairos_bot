#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Módulo de Logging
Configura e gerencia logs do sistema
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config.settings import LOGGING_CONFIG, LOGS_DIR, FILE_PATTERNS

def setup_logging():
    """Configura o sistema de logging"""
    # Cria diretório de logs se não existir
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo de log com data
    date = datetime.now().strftime('%Y%m%d')
    log_filename = FILE_PATTERNS['log_file'].format(date=date)
    log_filepath = LOGS_DIR / log_filename
    
    # Configuração do formatter
    formatter = logging.Formatter(
        fmt=LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['date_format']
    )
    
    # Configuração do logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    
    # Remove handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(
        log_filepath, 
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(f"Sistema de logging configurado - Arquivo: {log_filename}")
    
    return str(log_filepath)

def get_logger(name):
    """Retorna um logger configurado para o módulo especificado"""
    return logging.getLogger(name)

def log_performance(func):
    """Decorator para medir performance de funções"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__} executada em {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} falhou após {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

def log_async_performance(func):
    """Decorator para medir performance de funções assíncronas"""
    import time
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__} executada em {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} falhou após {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

class LogContext:
    """Context manager para logging com contexto específico"""
    
    def __init__(self, logger, operation_name, level=logging.INFO):
        self.logger = logger
        self.operation_name = operation_name
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"🚀 Iniciando: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        
        if exc_type is None:
            self.logger.log(self.level, f"✅ Concluído: {self.operation_name} ({duration.total_seconds():.2f}s)")
        else:
            self.logger.error(f"❌ Falhou: {self.operation_name} ({duration.total_seconds():.2f}s) - {exc_val}")
        
        return False  # Não suprimir exceções

# Configuração automática quando o módulo é importado
if not logging.getLogger().handlers:
    setup_logging()