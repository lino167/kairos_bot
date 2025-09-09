#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAIROS - Analisador Inteligente de Mercados de Apostas

Este módulo implementa a estratégia de dois níveis:
1. Análise Preliminar (Filtro Rápido) - Identifica "sinais de fumaça"
2. Análise Profunda (IA Gemini) - Investiga se há "fogo" real

Baseado na documentação do Excapper para máxima eficiência.
"""

import json
import sys
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Adicionar o diretório pai ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import LEAGUE_TIERS, ANALYSIS_RULES_BY_TIER

def determine_league_tier(league_name: str) -> str:
    """Determina o tier de uma liga baseado nas configurações.
    
    Args:
        league_name: Nome da liga
        
    Returns:
        str: 'tier1', 'tier2' ou 'tier3' (padrão)
    """
    if not league_name:
        return 'tier3'
    
    # Verificar tier1
    for tier1_league in LEAGUE_TIERS['tier1']:
        if tier1_league.lower() in league_name.lower():
            return 'tier1'
    
    # Verificar tier2
    for tier2_league in LEAGUE_TIERS['tier2']:
        if tier2_league.lower() in league_name.lower():
            return 'tier2'
    
    # Padrão é tier3
    return 'tier3'

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

@dataclass
class MarketSignal:
    """Representa um sinal detectado na análise preliminar."""
    signal_type: str  # 'money_way', 'drop_odds', 'sharp_bet'
    strength: float   # 0.0 a 1.0
    description: str
    market_name: str
    volume: Optional[int] = None
    odds_change: Optional[float] = None
    time_detected: Optional[str] = None

class PreliminaryAnalyzer:
    """Analisador preliminar - Filtro rápido para identificar sinais de oportunidade."""
    
    def __init__(self, tier_config: Optional[Dict] = None):
        if tier_config:
            min_volume = tier_config.get('min_volume', 5000)
            min_drop_percent = abs(tier_config.get('min_odds_drop_percent', -0.05)) * 100  # Converter para %
        else:
            min_volume = 5000
            min_drop_percent = 5
            
        self.config = {
            'money_way': {
                'min_volume': min_volume,      # Volume mínimo baseado no tier
                'high_volume': min_volume * 3,    # Volume alto (3x o mínimo)
                'very_high_volume': min_volume * 6 # Volume muito alto (6x o mínimo)
            },
            'drop_odds': {
                'min_drop_percent': min_drop_percent,   # Queda mínima baseada no tier
                'significant_drop': min_drop_percent * 2,  # Queda significativa (2x)
                'major_drop': min_drop_percent * 4         # Queda major (4x)
            },
            'sharp_bet': {
                'min_increase_percent': 15,  # Aumento mínimo de 15%
                'significant_increase': 30,  # Aumento significativo de 30%
                'major_increase': 50         # Aumento major de 50%
            }
        }
    
    def analyze_markets_preliminary(self, market_data: List[Dict]) -> List[MarketSignal]:
        """Análise preliminar de todos os mercados - Identifica sinais de fumaça."""
        print("[KAIROS] 🔍 Iniciando análise preliminar (filtro rápido)...")
        
        signals = []
        
        for market in market_data:
            market_signals = self._analyze_market_signals(market)
            signals.extend(market_signals)
        
        # Filtrar apenas sinais significativos
        significant_signals = [s for s in signals if s.strength >= 0.6]
        
        print(f"[KAIROS] 📊 Análise preliminar concluída: {len(significant_signals)} sinais detectados")
        return significant_signals
    
    def _analyze_market_signals(self, market: Dict) -> List[MarketSignal]:
        """Analisa um mercado individual em busca dos três sinais principais."""
        market_name = market.get('market_name', '')
        selections = market.get('selections', [])
        
        # Extrair dados do mercado
        market_data = self._extract_market_data(selections)
        
        signals = []
        
        # Sinal 1: Money Way (Alto Volume)
        money_signal = self._detect_money_way(market_name, market_data)
        if money_signal:
            signals.append(money_signal)
        
        # Sinal 2: Drop Odds (Queda de Odds)
        drop_signal = self._detect_drop_odds(market_name, market_data)
        if drop_signal:
            signals.append(drop_signal)
        
        # Sinal 3: Sharp Bet (Dinheiro Súbito)
        sharp_signal = self._detect_sharp_bet(market_name, market_data)
        if sharp_signal:
            signals.append(sharp_signal)
        
        return signals
    
    def _detect_money_way(self, market_name: str, data: Dict) -> Optional[MarketSignal]:
        """Detecta sinal de Money Way - Alto volume de dinheiro."""
        volume = self._parse_volume(data.get('volume'))
        
        if not volume:
            return None
        
        config = self.config['money_way']
        
        if volume >= config['very_high_volume']:
            strength = 1.0
            description = f"Volume muito alto: {volume}€ (>{config['very_high_volume']}€)"
        elif volume >= config['high_volume']:
            strength = 0.8
            description = f"Volume alto: {volume}€ (>{config['high_volume']}€)"
        elif volume >= config['min_volume']:
            strength = 0.6
            description = f"Volume significativo: {volume}€ (>{config['min_volume']}€)"
        else:
            return None
        
        return MarketSignal(
            signal_type='money_way',
            strength=strength,
            description=description,
            market_name=market_name,
            volume=volume,
            time_detected=datetime.now().strftime('%H:%M:%S')
        )
    
    def _detect_drop_odds(self, market_name: str, data: Dict) -> Optional[MarketSignal]:
        """Detecta sinal de Drop Odds - Queda significativa nas odds."""
        # Para implementar este sinal, precisaríamos de dados históricos das odds
        # Por enquanto, vamos simular baseado em dados de 'change' se disponível
        
        change_data = data.get('change')
        percent_data = data.get('percent')
        
        if not change_data and not percent_data:
            return None
        
        # Tentar extrair porcentagem de queda
        drop_percent = None
        
        if percent_data and isinstance(percent_data, str):
            try:
                # Extrair número da string (ex: "-15%" -> 15)
                if '%' in percent_data and '-' in percent_data:
                    drop_percent = abs(float(percent_data.replace('%', '').replace('-', '')))
            except:
                pass
        
        if not drop_percent:
            return None
        
        config = self.config['drop_odds']
        
        if drop_percent >= config['major_drop']:
            strength = 1.0
            description = f"Queda major nas odds: -{drop_percent}% (>{config['major_drop']}%)"
        elif drop_percent >= config['significant_drop']:
            strength = 0.8
            description = f"Queda significativa: -{drop_percent}% (>{config['significant_drop']}%)"
        elif drop_percent >= config['min_drop_percent']:
            strength = 0.6
            description = f"Queda detectada: -{drop_percent}% (>{config['min_drop_percent']}%)"
        else:
            return None
        
        return MarketSignal(
            signal_type='drop_odds',
            strength=strength,
            description=description,
            market_name=market_name,
            odds_change=-drop_percent,
            time_detected=datetime.now().strftime('%H:%M:%S')
        )
    
    def _detect_sharp_bet(self, market_name: str, data: Dict) -> Optional[MarketSignal]:
        """Detecta sinal de Sharp Bet - Aumento súbito de dinheiro."""
        # Para implementar completamente, precisaríamos de dados temporais
        # Por enquanto, vamos usar indicadores indiretos como tipo 'live' + volume alto
        
        volume = self._parse_volume(data.get('volume'))
        market_type = data.get('type')
        
        if not volume or market_type != 'live':
            return None
        
        # Em mercados ao vivo, volume alto pode indicar movimento súbito
        config = self.config['sharp_bet']
        
        if volume >= 20000:  # Volume muito alto em live
            strength = 0.9
            description = f"Possível sharp bet: {volume}€ em mercado ao vivo"
        elif volume >= 10000:  # Volume alto em live
            strength = 0.7
            description = f"Movimento suspeito: {volume}€ em mercado ao vivo"
        else:
            return None
        
        return MarketSignal(
            signal_type='sharp_bet',
            strength=strength,
            description=description,
            market_name=market_name,
            volume=volume,
            time_detected=datetime.now().strftime('%H:%M:%S')
        )
    
    def _extract_market_data(self, selections: List[Dict]) -> Dict:
        """Extrai dados estruturados das seleções de um mercado."""
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
    
    def _parse_volume(self, volume_str) -> Optional[int]:
        """Converte string de volume para inteiro."""
        if not volume_str:
            return None
        
        try:
            # Remove símbolos e converte (ex: "45000€" -> 45000)
            volume_clean = str(volume_str).replace('€', '').replace(',', '').replace('.', '')
            return int(volume_clean)
        except (ValueError, TypeError):
            return None

class KairosAnalyzer:
    """Analisador inteligente de mercados - Estratégia de dois níveis."""
    
    def __init__(self):
        self.confidence_thresholds = {
            'alto': 0.8,
            'medio': 0.6,
            'baixo': 0.4
        }
        self.preliminary_analyzer = PreliminaryAnalyzer()
    
    def analyze_markets_two_tier(self, market_data: List[Dict]) -> Tuple[List[MarketSignal], Optional[BettingOpportunity]]:
        """Análise de dois níveis: Preliminar + Profunda (quando necessário).
        
        Returns:
            Tuple[List[MarketSignal], Optional[BettingOpportunity]]: 
            - Lista de sinais detectados na análise preliminar
            - Oportunidade identificada na análise profunda (se aplicável)
        """
        print("[KAIROS] 🎯 Iniciando análise de dois níveis...")
        
        # Nível 1: Análise Preliminar (Filtro Rápido)
        signals = self.preliminary_analyzer.analyze_markets_preliminary(market_data)
        
        if not signals:
            print("[KAIROS] ❌ Nenhum sinal detectado na análise preliminar")
            return [], BettingOpportunity(
                found=False,
                market="N/A",
                selection="N/A",
                justification="Análise preliminar não detectou sinais significativos nos mercados disponíveis.",
                confidence_level="Baixo"
            )
        
        print(f"[KAIROS] ✅ {len(signals)} sinais detectados! Iniciando análise profunda...")
        
        # Nível 2: Análise Profunda (apenas nos mercados com sinais)
        markets_with_signals = self._filter_markets_with_signals(market_data, signals)
        deep_analysis = self.analyze_markets(markets_with_signals)
        
        return signals, deep_analysis
    
    def _filter_markets_with_signals(self, market_data: List[Dict], signals: List[MarketSignal]) -> List[Dict]:
        """Filtra apenas os mercados que tiveram sinais detectados."""
        signal_markets = {signal.market_name for signal in signals}
        return [market for market in market_data if market.get('market_name') in signal_markets]
    
    def get_analysis_summary(self, signals: List[MarketSignal], opportunity: Optional[BettingOpportunity]) -> str:
        """Gera um resumo completo da análise de dois níveis."""
        summary_parts = []
        
        # Resumo dos sinais
        if signals:
            summary_parts.append("🔍 **SINAIS DETECTADOS (Análise Preliminar):**")
            
            signal_counts = {}
            for signal in signals:
                signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
            
            for signal_type, count in signal_counts.items():
                type_name = {
                    'money_way': 'Money Way (Alto Volume)',
                    'drop_odds': 'Drop Odds (Queda de Odds)',
                    'sharp_bet': 'Sharp Bet (Dinheiro Súbito)'
                }.get(signal_type, signal_type)
                summary_parts.append(f"• {type_name}: {count} mercado(s)")
            
            # Detalhes dos sinais mais fortes
            strong_signals = [s for s in signals if s.strength >= 0.8]
            if strong_signals:
                summary_parts.append("\n🚨 **SINAIS FORTES:**")
                for signal in strong_signals[:3]:  # Top 3
                    summary_parts.append(f"• {signal.market_name}: {signal.description}")
        
        # Resultado da análise profunda
        summary_parts.append("\n🧠 **ANÁLISE PROFUNDA (IA):**")
        if opportunity and opportunity.found:
            summary_parts.append(f"✅ **OPORTUNIDADE IDENTIFICADA**")
            summary_parts.append(f"• Mercado: {opportunity.market}")
            summary_parts.append(f"• Seleção: {opportunity.selection}")
            summary_parts.append(f"• Confiança: {opportunity.confidence_level}")
            summary_parts.append(f"• Justificativa: {opportunity.justification}")
        else:
            summary_parts.append("❌ Nenhuma oportunidade clara identificada após análise profunda")
        
        return "\n".join(summary_parts)
        
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

def preliminary_analysis(game_data: dict, market_data: list, config: dict) -> list:
    """Análise preliminar contextual baseada no tier da liga.
    
    Args:
        game_data: Dados do jogo contendo informações da liga
        market_data: Lista de mercados para análise
        config: Configurações do sistema (deve conter LEAGUE_TIERS e ANALYSIS_RULES_BY_TIER)
        
    Returns:
        list: Lista de oportunidades detectadas com triggered_signal
    """
    # Determinar o tier da liga
    league_name = game_data.get('league', '')
    tier = determine_league_tier(league_name)
    
    print(f"[KAIROS] 🏆 Liga: {league_name} | Tier: {tier.upper()}")
    
    # Selecionar regras baseadas no tier
    tier_rules = config['ANALYSIS_RULES_BY_TIER'][tier]
    print(f"[KAIROS] ⚙️ Regras {tier}: Volume mín: {tier_rules['min_volume']}€, Queda mín: {tier_rules['min_odds_drop_percent']*100}%")
    
    # Criar analisador preliminar com configurações do tier
    analyzer = PreliminaryAnalyzer(tier_config=tier_rules)
    
    # Executar análise preliminar
    signals = analyzer.analyze_markets_preliminary(market_data)
    
    # Converter sinais para formato de oportunidades com triggered_signal
    opportunities = []
    for signal in signals:
        opportunity = {
            'market_name': signal.market_name,
            'signal_type': signal.signal_type,
            'strength': signal.strength,
            'description': signal.description,
            'triggered_signal': signal.signal_type,  # Campo solicitado
            'volume': signal.volume,
            'odds_change': signal.odds_change,
            'time_detected': signal.time_detected,
            'tier': tier,
            'league': league_name
        }
        opportunities.append(opportunity)
    
    print(f"[KAIROS] 📊 Análise preliminar {tier}: {len(opportunities)} oportunidades detectadas")
    return opportunities

# Função principal para uso externo
def analyze_betting_opportunity(market_data: List[Dict]) -> str:
    """
    Função de conveniência para análise de oportunidades - Estratégia de dois níveis.
    
    Args:
        market_data: Lista de mercados com dados das seleções
        
    Returns:
        str: Resultado formatado da análise completa
    """
    analyzer = KairosAnalyzer()
    signals, opportunity = analyzer.analyze_markets_two_tier(market_data)
    return analyzer.get_analysis_summary(signals, opportunity)

def analyze_betting_opportunity_legacy(market_data: List[Dict]) -> str:
    """
    Função legada - Análise tradicional (apenas análise profunda).
    Mantida para compatibilidade.
    """
    analyzer = KairosAnalyzer()
    opportunity = analyzer.analyze_markets(market_data)
    return analyzer.format_analysis_result(opportunity)

if __name__ == "__main__":
    # Exemplo de uso da nova análise contextual por tiers
    
    # Dados do jogo com diferentes ligas para teste
    game_data_tier1 = {
        'league': 'Premier League',  # Tier 1
        'teams': 'Manchester City vs Liverpool',
        'datetime': '2024-01-15 16:30:00'
    }
    
    game_data_tier2 = {
        'league': 'Brasileirão Série A',  # Tier 2
        'teams': 'Flamengo vs Palmeiras',
        'datetime': '2024-01-15 19:00:00'
    }
    
    game_data_tier3 = {
        'league': 'Liga Portuguesa',  # Tier 3 (padrão)
        'teams': 'Benfica vs Porto',
        'datetime': '2024-01-15 20:00:00'
    }
    
    # Dados de mercados para teste
    sample_data = [
        {
            "market_name": "Match Odds",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Summ", "odds": "25000€"},  # Alto volume - Money Way
                {"name": "Odds", "odds": 1.85},
                {"name": "Percent", "odds": "-12%"}  # Queda de odds - Drop Odds
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575347"
            }
        },
        {
            "market_name": "Over/Under 2.5 Goals",
            "selections": [
                {"name": "Type", "odds": "pre"},
                {"name": "Summ", "odds": "8000€"},   # Volume moderado
                {"name": "Odds", "odds": 2.10}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575348"
            }
        },
        {
            "market_name": "Both Teams to Score",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Summ", "odds": "2000€"},  # Volume baixo para teste tier 3
                {"name": "Odds", "odds": 1.95}
            ],
            "links": {
                "betfair_url": "https://www.betfair.com/exchange/plus/football/market/1.247575349"
            }
        }
    ]
    
    # Configurações para teste
    test_config = {
        'LEAGUE_TIERS': LEAGUE_TIERS,
        'ANALYSIS_RULES_BY_TIER': ANALYSIS_RULES_BY_TIER
    }
    
    print("=" * 80)
    print("🤖 KAIROS - DEMONSTRAÇÃO DA ANÁLISE CONTEXTUAL POR TIERS")
    print("=" * 80)
    
    # Teste com diferentes tiers de liga
    print("\n🏆 TESTE TIER 1 - PREMIER LEAGUE (Regras mais restritivas)")
    print("-" * 60)
    tier1_opportunities = preliminary_analysis(game_data_tier1, sample_data, test_config)
    print(f"Oportunidades detectadas: {len(tier1_opportunities)}")
    for opp in tier1_opportunities:
        print(f"  • {opp['market_name']}: {opp['description']} (Força: {opp['strength']:.2f})")
    
    print("\n🏆 TESTE TIER 2 - BRASILEIRÃO (Regras intermediárias)")
    print("-" * 60)
    tier2_opportunities = preliminary_analysis(game_data_tier2, sample_data, test_config)
    print(f"Oportunidades detectadas: {len(tier2_opportunities)}")
    for opp in tier2_opportunities:
        print(f"  • {opp['market_name']}: {opp['description']} (Força: {opp['strength']:.2f})")
    
    print("\n🏆 TESTE TIER 3 - LIGA PORTUGUESA (Regras mais flexíveis)")
    print("-" * 60)
    tier3_opportunities = preliminary_analysis(game_data_tier3, sample_data, test_config)
    print(f"Oportunidades detectadas: {len(tier3_opportunities)}")
    for opp in tier3_opportunities:
        print(f"  • {opp['market_name']}: {opp['description']} (Força: {opp['strength']:.2f})")
    
    print("\n" + "=" * 80)
    print("🤖 DEMONSTRAÇÃO DA ESTRATÉGIA DE DOIS NÍVEIS (Tier 1)")
    print("=" * 80)
    
    # Análise com a nova estratégia (usando dados tier 1)
    result = analyze_betting_opportunity(sample_data)
    print(result)
    
    print("\n" + "=" * 80)
    print("📊 COMPARAÇÃO: Análise Tradicional (Legada)")
    print("=" * 80)
    
    # Comparação com análise tradicional
    legacy_result = analyze_betting_opportunity_legacy(sample_data)
    print(legacy_result)