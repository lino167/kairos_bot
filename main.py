#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS BOT - Script Principal
Orquestra todas as operações do sistema de extração e investigação de jogos
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    ensure_directories, validate_config, MAIN_CONFIG,
    DATA_DIR, LOGS_DIR, SCREENSHOTS_DIR
)
from utils.logger import setup_logging, get_logger, LogContext
from utils.helpers import format_timestamp, get_file_info
from modules.extractor import GameExtractor
from modules.investigator import GameInvestigator

class KairosBot:
    """Classe principal do KAIROS BOT"""
    
    def __init__(self):
        # Configura logging
        self.log_file = setup_logging()
        self.logger = get_logger(__name__)
        
        # Cria diretórios necessários
        ensure_directories()
        
        # Valida configurações
        validate_config()
        
        self.logger.info("🚀 KAIROS BOT inicializado")
        self.logger.info(f"📝 Log file: {self.log_file}")
    
    async def extract_games(self, save_screenshots=False):
        """Executa extração de jogos"""
        with LogContext(self.logger, "Extração de jogos"):
            extractor = GameExtractor()
            
            # Configura screenshots se solicitado
            if save_screenshots:
                from config.settings import EXTRACTION_CONFIG
                EXTRACTION_CONFIG['save_screenshots'] = True
            
            return await extractor.run_extraction()
    
    async def investigate_games(self, games_file_path):
        """Executa investigação de jogos"""
        with LogContext(self.logger, "Investigação de jogos"):
            investigator = GameInvestigator()
            return await investigator.run_investigation(games_file_path)
    
    async def full_pipeline(self, investigate=True, save_screenshots=False):
        """Executa pipeline completo: extração + investigação"""
        with LogContext(self.logger, "Pipeline completo"):
            # Etapa 1: Extração
            self.logger.info("🎯 Etapa 1: Extraindo dados dos jogos")
            games_file = await self.extract_games(save_screenshots=save_screenshots)
            
            if not games_file:
                self.logger.error("❌ Falha na extração de jogos")
                return None
            
            results = {'extraction_file': games_file}
            
            # Etapa 2: Investigação (opcional)
            if investigate:
                self.logger.info("🔍 Etapa 2: Investigando jogos extraídos")
                investigation_file = await self.investigate_games(games_file)
                
                if investigation_file:
                    results['investigation_file'] = investigation_file
                else:
                    self.logger.warning("⚠️ Investigação falhou, mas extração foi bem-sucedida")
            
            return results
    
    def list_data_files(self):
        """Lista arquivos de dados disponíveis"""
        print("\n" + "="*60)
        print("ARQUIVOS DE DADOS DISPONÍVEIS")
        print("="*60)
        
        # Arquivos de extração
        extraction_files = list(DATA_DIR.glob("games_data_*.json"))
        if extraction_files:
            print("\n📊 Arquivos de Extração:")
            for i, file_path in enumerate(sorted(extraction_files, reverse=True)[:5]):
                info = get_file_info(file_path)
                print(f"   {i+1}. {info['name']}")
                print(f"      📅 Modificado: {info['modified'].strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"      📏 Tamanho: {info['size_formatted']}")
        
        # Arquivos de investigação
        investigation_files = list(DATA_DIR.glob("investigation_*.json"))
        if investigation_files:
            print("\n🔍 Arquivos de Investigação:")
            for i, file_path in enumerate(sorted(investigation_files, reverse=True)[:5]):
                info = get_file_info(file_path)
                print(f"   {i+1}. {info['name']}")
                print(f"      📅 Modificado: {info['modified'].strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"      📏 Tamanho: {info['size_formatted']}")
        
        # Screenshots
        screenshot_files = list(SCREENSHOTS_DIR.glob("*.png"))
        if screenshot_files:
            print(f"\n📸 Screenshots: {len(screenshot_files)} arquivos")
        
        # Logs
        log_files = list(LOGS_DIR.glob("*.log"))
        if log_files:
            print(f"\n📝 Logs: {len(log_files)} arquivos")
    
    def show_system_info(self):
        """Mostra informações do sistema"""
        print("\n" + "="*60)
        print("INFORMAÇÕES DO SISTEMA KAIROS BOT")
        print("="*60)
        
        print(f"🤖 Versão: {MAIN_CONFIG['version']}")
        print(f"👤 Autor: {MAIN_CONFIG['author']}")
        print(f"📅 Data atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        print(f"\n📁 Diretórios:")
        print(f"   • Dados: {DATA_DIR}")
        print(f"   • Logs: {LOGS_DIR}")
        print(f"   • Screenshots: {SCREENSHOTS_DIR}")
        
        print(f"\n⚙️ Configurações principais:")
        print(f"   • Modo headless: {MAIN_CONFIG['headless_mode']}")
        print(f"   • Timeout padrão: {MAIN_CONFIG['default_timeout']}s")
        print(f"   • Max jogos por execução: {MAIN_CONFIG['max_games_per_run']}")
    
    def cleanup(self):
        """Limpeza final"""
        self.logger.info("🧹 Limpeza concluída")
        print(f"\n📝 Log salvo em: {self.log_file}")

def create_argument_parser():
    """Cria parser de argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description="KAIROS BOT - Sistema de extração e investigação de jogos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py extract                    # Apenas extração
  python main.py extract --screenshots     # Extração com screenshots
  python main.py investigate arquivo.json  # Apenas investigação
  python main.py full                       # Pipeline completo
  python main.py full --no-investigate     # Só extração no pipeline
  python main.py list                       # Lista arquivos de dados
  python main.py info                       # Informações do sistema
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando extract
    extract_parser = subparsers.add_parser('extract', help='Extrai dados dos jogos')
    extract_parser.add_argument(
        '--screenshots', 
        action='store_true',
        help='Salva screenshots durante a extração'
    )
    
    # Comando investigate
    investigate_parser = subparsers.add_parser('investigate', help='Investiga jogos de um arquivo')
    investigate_parser.add_argument(
        'games_file',
        help='Caminho para o arquivo de jogos extraídos'
    )
    
    # Comando full
    full_parser = subparsers.add_parser('full', help='Executa pipeline completo')
    full_parser.add_argument(
        '--no-investigate',
        action='store_true',
        help='Pula a etapa de investigação'
    )
    full_parser.add_argument(
        '--screenshots',
        action='store_true',
        help='Salva screenshots durante a extração'
    )
    
    # Comando list
    subparsers.add_parser('list', help='Lista arquivos de dados disponíveis')
    
    # Comando info
    subparsers.add_parser('info', help='Mostra informações do sistema')
    
    return parser

async def main():
    """Função principal"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Inicializa o bot
    bot = KairosBot()
    
    try:
        if args.command == 'extract':
            result = await bot.extract_games(save_screenshots=args.screenshots)
            if result:
                print(f"\n✅ Extração concluída: {result}")
            else:
                print("\n❌ Falha na extração")
                sys.exit(1)
        
        elif args.command == 'investigate':
            games_file = Path(args.games_file)
            if not games_file.exists():
                print(f"\n❌ Arquivo não encontrado: {games_file}")
                sys.exit(1)
            
            result = await bot.investigate_games(str(games_file))
            if result:
                print(f"\n✅ Investigação concluída: {result}")
            else:
                print("\n❌ Falha na investigação")
                sys.exit(1)
        
        elif args.command == 'full':
            investigate = not args.no_investigate
            results = await bot.full_pipeline(
                investigate=investigate,
                save_screenshots=args.screenshots
            )
            
            if results:
                print("\n✅ Pipeline concluído com sucesso!")
                print(f"📊 Extração: {results['extraction_file']}")
                if 'investigation_file' in results:
                    print(f"🔍 Investigação: {results['investigation_file']}")
            else:
                print("\n❌ Falha no pipeline")
                sys.exit(1)
        
        elif args.command == 'list':
            bot.list_data_files()
        
        elif args.command == 'info':
            bot.show_system_info()
    
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        bot.logger.error(f"Erro inesperado: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        bot.cleanup()

if __name__ == "__main__":
    # Verifica versão do Python
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ é necessário")
        sys.exit(1)
    
    # Executa função principal
    asyncio.run(main())