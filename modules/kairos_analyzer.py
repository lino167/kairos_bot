#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS - Analisador Inteligente de Mercados de Apostas

Este módulo implementa a IA KAIROS, especializada em análise de mercados
de apostas na Betfair para identificar oportunidades de valor.
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class BettingOpportunity:
    """Representa uma oportunidade de aposta identificada."""
    found: bool
    market: str
    selection: str
    justification: str
    confidence_level: str
    betfair_url: Optional[str] = None
    volume: Optional[str] = None
    odds: Optional[float] = None

class KairosAnalyzer:
    """Analisador inteligente de mercados de apostas da Betfair."""
    
    def __init__(self):
        self.confidence_thresholds = {
            'alto': 0.8,
            'medio': 0.6,
            'baixo': 0.4
        }
        
    def analyze_markets(self, market_data: List[Dict]) -> BettingOpportunity:
        """
        Analisa todos os mercados de uma partida e identifica a melhor oportunidade.
        
        Args:
            market_data: Lista de mercados com seleções, odds e links
            
        Returns:
            BettingOpportunity: A melhor oportunidade encontrada ou indicação de que não há
        """
        print("[KAIROS] 🧠 Iniciando análise inteligente de mercados...")
        
        if not market_data:
            return BettingOpportunity(
                found=False,
                market="N/A",
                selection="N/A",
                justification="Nenhum dado de mercado disponível para análise.",
                confidence_level="Baixo"
            )
        
        # Analisar cada mercado
        opportunities = []
        
        for market in market_data:
            opportunity = self._analyze_single_market(market)
            if opportunity:
                opportunities.append(opportunity)
        
        # Selecionar a melhor oportunidade
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x[1])  # Por score de confiança
            return best_opportunity[0]
        else:
            return BettingOpportunity(
                found=False,
                market="N/A",
                selection="N/A",
                justification="Após análise completa dos mercados disponíveis, não foram identificadas oportunidades claras de valor no momento atual.",
                confidence_level="Baixo"
            )
    
    def _analyze_single_market(self, market: Dict) -> Optional[Tuple[BettingOpportunity, float]]:
        """
        Analisa um mercado individual em busca de oportunidades.
        
        Args:
            market: Dados do mercado (nome, seleções, links)
            
        Returns:
            Tuple com a oportunidade e score de confiança, ou None
        """
        market_name = market.get('market_name', '')
        selections = market.get('selections', [])
        links = market.get('links', {})
        
        print(f"[KAIROS] 📊 Analisando mercado: {market_name}")
        
        # Extrair dados relevantes das seleções
        market_data = self._extract_market_data(selections)
        
        if not market_data:
            return None
        
        # Análises específicas por tipo de mercado
        if 'Match Odds' in market_name:
            return self._analyze_match_odds(market_name, market_data, links)
        elif 'Over/Under' in market_name:
            return self._analyze_over_under(market_name, market_data, links)
        elif 'Both teams to Score' in market_name:
            return self._analyze_btts(market_name, market_data, links)
        elif 'Half' in market_name:
            return self._analyze_half_markets(market_name, market_data, links)
        
        return None
    
    def _extract_market_data(self, selections: List[Dict]) -> Dict:
        """
        Extrai dados estruturados das seleções de um mercado.
        
        Args:
            selections: Lista de seleções com nomes e odds
            
        Returns:
            Dict com dados estruturados do mercado
        """
        data = {
            'type': None,
            'volume': None,
            'odds': None,
            'change': None,
            'percent': None,
            'time': None,
            'score': None
        }
        
        for selection in selections:
            name = selection.get('name', '').lower()
            value = selection.get('odds')
            
            if 'type' in name:
                data['type'] = value
            elif 'summ' in name:
                data['volume'] = value
            elif 'odds' in name and isinstance(value, (int, float)):
                data['odds'] = float(value)
            elif 'change' in name:
                data['change'] = value
            elif 'percent' in name:
                data['percent'] = value
            elif 'time' in name:
                data['time'] = value
            elif 'score' in name:
                data['score'] = value
        
        return data
    
    def _analyze_match_odds(self, market_name: str, data: Dict, links: Dict) -> Optional[Tuple[BettingOpportunity, float]]:
        """
        Analisa o mercado de Match Odds (1X2).
        """
        volume = self._parse_volume(data.get('volume'))
        odds = data.get('odds')
        market_type = data.get('type')
        
        if not volume or not odds:
            return None
        
        # Critérios para Match Odds
        confidence_score = 0.0
        justification_parts = []
        
        # Volume alto indica interesse
        if volume > 50000:
            confidence_score += 0.3
            justification_parts.append(f"Alto volume de {volume}€ indica forte interesse")
        elif volume > 20000:
            confidence_score += 0.2
            justification_parts.append(f"Volume moderado de {volume}€")
        
        # Odds em range interessante
        if 1.5 <= odds <= 2.5:
            confidence_score += 0.3
            justification_parts.append(f"Odds de {odds} em range de valor")
        
        # Mercado ao vivo tem mais dinâmica
        if market_type == 'live':
            confidence_score += 0.2
            justification_parts.append("Mercado ao vivo com potencial de movimento")
        
        if confidence_score >= 0.6:
            return (BettingOpportunity(
                found=True,
                market=market_name,
                selection="Favorito identificado",
                justification=f"Match Odds: {'. '.join(justification_parts)}.",
                confidence_level=self._get_confidence_level(confidence_score),
                betfair_url=links.get('betfair_url'),
                volume=f"{volume}€" if volume else None,
                odds=odds
            ), confidence_score)
        
        return None
    
    def _analyze_over_under(self, market_name: str, data: Dict, links: Dict) -> Optional[Tuple[BettingOpportunity, float]]:
        """
        Analisa mercados de Over/Under Goals.
        """
        volume = self._parse_volume(data.get('volume'))
        odds = data.get('odds')
        market_type = data.get('type')
        
        if not volume or not odds:
            return None
        
        confidence_score = 0.0
        justification_parts = []
        
        # Extrair linha de gols do nome do mercado
        goal_line = self._extract_goal_line(market_name)
        
        # Volume significativo
        if volume > 30000:
            confidence_score += 0.25
            justification_parts.append(f"Volume expressivo de {volume}€")
        
        # Odds atrativas para Over/Under
        if 1.8 <= odds <= 2.2:
            confidence_score += 0.35
            justification_parts.append(f"Odds equilibradas de {odds}")
        
        # Linhas de gols mais populares (2.5, 1.5)
        if goal_line in ['2.5', '1.5']:
            confidence_score += 0.2
            justification_parts.append(f"Linha {goal_line} com boa liquidez")
        
        # Mercado ao vivo
        if market_type == 'live':
            confidence_score += 0.15
            justification_parts.append("Dinâmica ao vivo favorável")
        
        if confidence_score >= 0.6:
            return (BettingOpportunity(
                found=True,
                market=market_name,
                selection=f"Over {goal_line}" if goal_line else "Over",
                justification=f"Over/Under: {'. '.join(justification_parts)}.",
                confidence_level=self._get_confidence_level(confidence_score),
                betfair_url=links.get('betfair_url'),
                volume=f"{volume}€" if volume else None,
                odds=odds
            ), confidence_score)
        
        return None
    
    def _analyze_btts(self, market_name: str, data: Dict, links: Dict) -> Optional[Tuple[BettingOpportunity, float]]:
        """
        Analisa mercado Both Teams to Score.
        """
        volume = self._parse_volume(data.get('volume'))
        odds = data.get('odds')
        
        if not volume or not odds:
            return None
        
        confidence_score = 0.0
        justification_parts = []
        
        # BTTS é mercado popular
        if volume > 15000:
            confidence_score += 0.3
            justification_parts.append(f"Volume de {volume}€ no BTTS")
        
        # Odds interessantes para BTTS
        if 1.6 <= odds <= 2.4:
            confidence_score += 0.4
            justification_parts.append(f"Odds atrativas de {odds}")
        
        if confidence_score >= 0.5:
            return (BettingOpportunity(
                found=True,
                market=market_name,
                selection="Yes" if odds < 2.0 else "No",
                justification=f"BTTS: {'. '.join(justification_parts)}.",
                confidence_level=self._get_confidence_level(confidence_score),
                betfair_url=links.get('betfair_url'),
                volume=f"{volume}€" if volume else None,
                odds=odds
            ), confidence_score)
        
        return None
    
    def _analyze_half_markets(self, market_name: str, data: Dict, links: Dict) -> Optional[Tuple[BettingOpportunity, float]]:
        """
        Analisa mercados de primeiro tempo.
        """
        volume = self._parse_volume(data.get('volume'))
        odds = data.get('odds')
        
        if not volume or not odds or volume < 10000:
            return None  # Mercados de HT precisam de volume mínimo
        
        confidence_score = 0.0
        justification_parts = []
        
        if volume > 20000:
            confidence_score += 0.25
            justification_parts.append(f"Volume HT de {volume}€")
        
        if 1.5 <= odds <= 3.0:
            confidence_score += 0.3
            justification_parts.append(f"Odds HT de {odds}")
        
        if confidence_score >= 0.4:
            return (BettingOpportunity(
                found=True,
                market=market_name,
                selection="Primeiro Tempo",
                justification=f"Half Time: {'. '.join(justification_parts)}.",
                confidence_level=self._get_confidence_level(confidence_score),
                betfair_url=links.get('betfair_url'),
                volume=f"{volume}€" if volume else None,
                odds=odds
            ), confidence_score)
        
        return None
    
    def _parse_volume(self, volume_str) -> Optional[int]:
        """
        Converte string de volume para número inteiro.
        
        Args:
            volume_str: String como "15040€" ou "15040 €"
            
        Returns:
            Valor numérico do volume ou None
        """
        if not volume_str:
            return None
        
        try:
            # Remove símbolos e espaços
            clean_str = str(volume_str).replace('€', '').replace(' ', '').replace(',', '')
            return int(float(clean_str))
        except (ValueError, TypeError):
            return None
    
    def _extract_goal_line(self, market_name: str) -> Optional[str]:
        """
        Extrai a linha de gols do nome do mercado.
        
        Args:
            market_name: Nome como "Over/Under 2.5 Goals"
            
        Returns:
            Linha de gols como "2.5" ou None
        """
        import re
        match = re.search(r'(\d+\.\d+)', market_name)
        return match.group(1) if match else None
    
    def _get_confidence_level(self, score: float) -> str:
        """
        Converte score numérico para nível de confiança.
        
        Args:
            score: Score de 0.0 a 1.0
            
        Returns:
            "Alto", "Médio" ou "Baixo"
        """
        if score >= self.confidence_thresholds['alto']:
            return "Alto"
        elif score >= self.confidence_thresholds['medio']:
            return "Médio"
        else:
            return "Baixo"
    
    def format_analysis_result(self, opportunity: BettingOpportunity) -> str:
        """
        Formata o resultado da análise no formato solicitado.
        
        Args:
            opportunity: Oportunidade identificada
            
        Returns:
            String formatada com o resultado
        """
        result = f"""
🎯 **ANÁLISE KAIROS - RESULTADO**

1. **Oportunidade Encontrada:** {'Sim' if opportunity.found else 'Não'}
2. **Mercado Sugerido:** {opportunity.market}
3. **Seleção:** {opportunity.selection}
4. **Justificativa da Análise:** {opportunity.justification}
5. **Nível de Confiança:** {opportunity.confidence_level}
"""
        
        if opportunity.betfair_url:
            result += f"\n🔗 **Link Betfair:** {opportunity.betfair_url}"
        
        if opportunity.volume:
            result += f"\n💰 **Volume:** {opportunity.volume}"
        
        if opportunity.odds:
            result += f"\n📊 **Odds:** {opportunity.odds}"
        
        return result

# Função principal para uso externo
def analyze_betting_opportunity(market_data: List[Dict]) -> str:
    """
    Função principal para análise de oportunidades de aposta.
    
    Args:
        market_data: Lista de mercados extraídos pelo scraper
        
    Returns:
        String formatada com a análise completa
    """
    analyzer = KairosAnalyzer()
    opportunity = analyzer.analyze_markets(market_data)
    return analyzer.format_analysis_result(opportunity)

if __name__ == "__main__":
    # Teste com dados de exemplo
    sample_data = [
        {
            "market_name": "Match Odds",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Summ", "odds": "45000€"},
                {"name": "Odds", "odds": 1.85}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575347"
            }
        }
    ]
    
    result = analyze_betting_opportunity(sample_data)
    print(result)