#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from modules.extractor import GameExtractor
from utils.helpers import validate_game_data
from config.settings import DATA_CONFIG

async def test_validation():
    """Testa a validação dos dados extraídos"""
    print("Campos obrigatórios:", DATA_CONFIG['required_fields'])
    
    extractor = GameExtractor()
    await extractor.setup_browser()
    await extractor.navigate_to_site()
    
    # Pega as primeiras linhas de jogos
    game_rows = await extractor.page.query_selector_all('tr.a_link')
    
    if game_rows:
        print(f"\nEncontradas {len(game_rows)} linhas de jogos")
        
        # Testa os primeiros 3 jogos
        for i in range(min(3, len(game_rows))):
            print(f"\n--- JOGO {i+1} ---")
            game_data = await extractor._extract_single_game(game_rows[i], i)
            
            if game_data:
                print("Dados extraídos:")
                for field in DATA_CONFIG['required_fields']:
                    value = game_data.get(field)
                    print(f"  {field}: {repr(value)}")
                
                is_valid = validate_game_data(game_data)
                print(f"\nValidação: {is_valid}")
                
                # Verifica cada campo obrigatório
                for field in DATA_CONFIG['required_fields']:
                    value = game_data.get(field)
                    if not value:
                        print(f"  ❌ Campo '{field}' está vazio ou None")
                    else:
                        print(f"  ✅ Campo '{field}' OK")
            else:
                print("Nenhum dado extraído")
    
    await extractor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_validation())