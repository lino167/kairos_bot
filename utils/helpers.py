#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Funções Auxiliares
Utilitários e funções de apoio para o sistema
"""

import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

from config.settings import DATA_CONFIG, FILE_CONFIG

def format_timestamp(dt=None, format_type='filename'):
    """Formata timestamp para diferentes usos"""
    if dt is None:
        dt = datetime.now()
    
    formats = {
        'filename': '%Y%m%d_%H%M%S',
        'display': '%d/%m/%Y %H:%M:%S',
        'iso': '%Y-%m-%dT%H:%M:%S',
        'date_only': '%Y-%m-%d',
        'time_only': '%H:%M:%S'
    }
    
    return dt.strftime(formats.get(format_type, formats['filename']))

def validate_game_data(game_data: Dict[str, Any]) -> bool:
    """Valida se os dados do jogo estão completos e corretos"""
    required_fields = DATA_CONFIG['required_fields']
    
    # Verifica campos obrigatórios
    for field in required_fields:
        if field not in game_data or not game_data[field]:
            return False
    
    # Validações específicas
    if not game_data.get('teams') or ' - ' not in game_data['teams']:
        return False
    
    if game_data.get('money_numeric', 0) < 0:
        return False
    
    # Valida formato da data/hora
    if not validate_datetime_format(game_data.get('date_time', '')):
        return False
    
    return True

def validate_datetime_format(date_time_str: str) -> bool:
    """Valida formato de data/hora"""
    if not date_time_str:
        return False
    
    # Padrões comuns de data/hora
    patterns = [
        r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}',  # DD/MM/YYYY HH:MM
        r'\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}',  # DD-MM-YYYY HH:MM
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # YYYY-MM-DD HH:MM
        r'\d{2}/\d{2}\s+\d{2}:\d{2}',        # DD/MM HH:MM
    ]
    
    return any(re.match(pattern, date_time_str.strip()) for pattern in patterns)

def clean_text(text: str) -> str:
    """Limpa e normaliza texto"""
    if not text:
        return ''
    
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove caracteres especiais problemáticos
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u200b', '')  # Zero-width space
    
    return text

def extract_money_value(money_str: str) -> int:
    """Extrai valor monetário numérico de string"""
    if not money_str:
        return 0
    
    # Procura por padrões de dinheiro
    patterns = [
        r'([0-9,]+)\s*€',
        r'€\s*([0-9,]+)',
        r'([0-9,]+)\s*EUR',
        r'([0-9,]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, money_str)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                return int(value_str)
            except ValueError:
                continue
    
    return 0

def validate_url(url: str, base_url: str = None) -> bool:
    """Valida se uma URL é válida"""
    if not url:
        return False
    
    try:
        # Se é uma URL relativa, junta com base_url
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
    except Exception:
        return False

def generate_game_hash(game_data: Dict[str, Any]) -> str:
    """Gera hash único para um jogo baseado em seus dados"""
    # Campos que identificam unicamente um jogo
    key_fields = ['date_time', 'teams', 'league']
    
    hash_string = '|'.join(
        str(game_data.get(field, '')) for field in key_fields
    )
    
    return hashlib.md5(hash_string.encode()).hexdigest()[:12]

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Carrega arquivo JSON com tratamento de erros"""
    try:
        with open(filepath, 'r', encoding=FILE_CONFIG['encoding']) as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON: {e}")
    except Exception as e:
        raise Exception(f"Erro ao carregar arquivo: {e}")

def save_json_file(data: Dict[str, Any], filepath: Path) -> None:
    """Salva dados em arquivo JSON"""
    try:
        # Cria diretório se não existir
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding=FILE_CONFIG['encoding']) as f:
            json.dump(
                data, f,
                indent=FILE_CONFIG['json_indent'],
                ensure_ascii=FILE_CONFIG['ensure_ascii']
            )
    except Exception as e:
        raise Exception(f"Erro ao salvar arquivo: {e}")

def filter_games_by_criteria(games: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
    """Filtra jogos baseado em critérios específicos"""
    filtered_games = []
    
    for game in games:
        include_game = True
        
        # Filtro por liga
        if 'leagues' in criteria and criteria['leagues']:
            if game.get('league', '').lower() not in [l.lower() for l in criteria['leagues']]:
                include_game = False
        
        # Filtro por país
        if 'countries' in criteria and criteria['countries']:
            country_alt = game.get('country', {}).get('alt', '').lower()
            if country_alt not in [c.lower() for c in criteria['countries']]:
                include_game = False
        
        # Filtro por valor mínimo
        if 'min_money' in criteria:
            if game.get('money_numeric', 0) < criteria['min_money']:
                include_game = False
        
        # Filtro por valor máximo
        if 'max_money' in criteria:
            if game.get('money_numeric', 0) > criteria['max_money']:
                include_game = False
        
        # Filtro por time específico
        if 'team_name' in criteria and criteria['team_name']:
            teams = game.get('teams', '').lower()
            if criteria['team_name'].lower() not in teams:
                include_game = False
        
        if include_game:
            filtered_games.append(game)
    
    return filtered_games

def calculate_statistics(games: List[Dict]) -> Dict[str, Any]:
    """Calcula estatísticas dos jogos"""
    if not games:
        return {}
    
    stats = {
        'total_games': len(games),
        'games_with_links': sum(1 for g in games if g.get('game_link')),
        'games_with_money': sum(1 for g in games if g.get('money_numeric', 0) > 0),
        'total_money': sum(g.get('money_numeric', 0) for g in games),
        'average_money': 0,
        'leagues': list(set(g.get('league', '') for g in games if g.get('league'))),
        'countries': list(set(
            g.get('country', {}).get('alt', '') 
            for g in games 
            if g.get('country', {}).get('alt')
        )),
        'teams': list(set(g.get('teams', '') for g in games if g.get('teams'))),
        'money_distribution': {}
    }
    
    # Calcula média de dinheiro
    money_games = [g for g in games if g.get('money_numeric', 0) > 0]
    if money_games:
        stats['average_money'] = sum(g['money_numeric'] for g in money_games) / len(money_games)
    
    # Distribuição de valores
    money_values = [g.get('money_numeric', 0) for g in games if g.get('money_numeric', 0) > 0]
    if money_values:
        stats['money_distribution'] = {
            'min': min(money_values),
            'max': max(money_values),
            'median': sorted(money_values)[len(money_values) // 2]
        }
    
    return stats

def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em formato legível"""
    if size_bytes == 0:
        return '0 B'
    
    size_names = ['B', 'KB', 'MB', 'GB']
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_info(filepath: Path) -> Dict[str, Any]:
    """Obtém informações detalhadas de um arquivo"""
    if not filepath.exists():
        return {}
    
    stat = filepath.stat()
    
    return {
        'name': filepath.name,
        'path': str(filepath),
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'extension': filepath.suffix,
        'is_file': filepath.is_file(),
        'is_dir': filepath.is_dir()
    }

def create_backup_filename(original_path: Path) -> Path:
    """Cria nome de arquivo de backup"""
    timestamp = format_timestamp()
    stem = original_path.stem
    suffix = original_path.suffix
    
    backup_name = f"{stem}_backup_{timestamp}{suffix}"
    return original_path.parent / backup_name

def safe_filename(filename: str) -> str:
    """Cria nome de arquivo seguro removendo caracteres problemáticos"""
    # Remove caracteres não permitidos
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove espaços extras e pontos no final
    safe_chars = re.sub(r'\s+', '_', safe_chars.strip('. '))
    
    # Limita tamanho
    if len(safe_chars) > 200:
        safe_chars = safe_chars[:200]
    
    return safe_chars

def compare_game_data(game1: Dict, game2: Dict) -> Dict[str, Any]:
    """Compara dois jogos e retorna diferenças"""
    differences = {
        'are_same': True,
        'changed_fields': [],
        'details': {}
    }
    
    # Campos a comparar
    compare_fields = ['teams', 'league', 'money', 'date_time', 'country']
    
    for field in compare_fields:
        val1 = game1.get(field)
        val2 = game2.get(field)
        
        if val1 != val2:
            differences['are_same'] = False
            differences['changed_fields'].append(field)
            differences['details'][field] = {
                'old': val1,
                'new': val2
            }
    
    return differences