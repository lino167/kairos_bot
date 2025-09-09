#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integração com Google Gemini para Análise Avançada de Apostas

Este módulo utiliza a API do Google Gemini para fornecer análises
mais sofisticadas e insights sobre mercados de apostas.
"""

import json
import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Adicionar o diretório de configuração ao path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

try:
    import google.generativeai as genai
    from api_keys import get_gemini_api_key, validate_gemini_key, GEMINI_CONFIG
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Generative AI não instalado. Execute: pip install google-generativeai")

@dataclass
class GeminiAnalysis:
    """Resultado da análise do Gemini."""
    success: bool
    analysis: str
    confidence: float
    recommendations: List[str]
    risk_assessment: str
    market_insights: Dict[str, Any]
    error_message: Optional[str] = None

class GeminiAnalyzer:
    """Analisador avançado usando Google Gemini."""
    
    def __init__(self):
        self.model = None
        self.initialized = False
        
        if GEMINI_AVAILABLE and validate_gemini_key():
            try:
                # Configurar a API do Gemini
                genai.configure(api_key=get_gemini_api_key())
                self.model = genai.GenerativeModel(GEMINI_CONFIG['model'])
                self.initialized = True
                print("✅ Gemini inicializado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao inicializar Gemini: {e}")
        else:
            print("⚠️ Gemini não disponível - usando análise local")
    
    def analyze_betting_markets(self, market_data: List[Dict], game_context: Dict = None) -> GeminiAnalysis:
        """
        Analisa mercados de apostas usando Gemini para insights avançados.
        
        Args:
            market_data: Dados dos mercados extraídos
            game_context: Contexto adicional do jogo (times, liga, etc.)
            
        Returns:
            GeminiAnalysis: Análise completa do Gemini
        """
        if not self.initialized:
            return self._fallback_analysis(market_data)
        
        try:
            # Preparar prompt para o Gemini
            prompt = self._create_analysis_prompt(market_data, game_context)
            
            # Gerar análise com Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_CONFIG['temperature'],
                    max_output_tokens=GEMINI_CONFIG['max_tokens']
                )
            )
            
            # Processar resposta
            return self._process_gemini_response(response.text)
            
        except Exception as e:
            print(f"❌ Erro na análise Gemini: {e}")
            return self._fallback_analysis(market_data, str(e))
    
    def _create_analysis_prompt(self, market_data: List[Dict], game_context: Dict = None) -> str:
        """
        Cria um prompt estruturado para análise do Gemini.
        
        Args:
            market_data: Dados dos mercados
            game_context: Contexto do jogo
            
        Returns:
            str: Prompt formatado para o Gemini
        """
        context_info = ""
        if game_context:
            context_info = f"""
**CONTEXTO DO JOGO:**
- Times: {game_context.get('teams', 'N/A')}
- Liga: {game_context.get('league', 'N/A')}
- Data/Hora: {game_context.get('datetime', 'N/A')}
- Status: {game_context.get('status', 'N/A')}
"""
        
        markets_info = ""
        for i, market in enumerate(market_data[:5], 1):  # Limitar a 5 mercados
            markets_info += f"""
**MERCADO {i}: {market.get('market_name', 'N/A')}**
"""
            for selection in market.get('selections', [])[:8]:  # Limitar seleções
                name = selection.get('name', 'N/A')
                odds = selection.get('odds', 'N/A')
                markets_info += f"- {name}: {odds}\n"
            
            if market.get('links', {}).get('betfair_url'):
                markets_info += f"- Betfair: {market['links']['betfair_url']}\n"
            markets_info += "\n"
        
        prompt = f"""
Você é KAIROS, uma IA especialista em análise de apostas esportivas da Betfair. Analise os dados abaixo e forneça insights profissionais.

{context_info}

**DADOS DOS MERCADOS:**
{markets_info}

**INSTRUÇÕES PARA ANÁLISE:**
1. Identifique padrões nos volumes e odds
2. Avalie oportunidades de valor
3. Considere riscos e volatilidade
4. Forneça recomendações específicas
5. Avalie o contexto temporal (se ao vivo)

**FORMATO DE RESPOSTA (JSON):**
{{
    "analysis": "Análise detalhada dos mercados e oportunidades identificadas",
    "confidence": 0.85,
    "recommendations": [
        "Recomendação específica 1",
        "Recomendação específica 2"
    ],
    "risk_assessment": "Avaliação de risco (Baixo/Médio/Alto)",
    "market_insights": {{
        "best_market": "Nome do melhor mercado",
        "volume_analysis": "Análise dos volumes",
        "odds_movement": "Análise do movimento das odds",
        "timing": "Melhor momento para apostar"
    }}
}}

Responda APENAS com o JSON válido, sem texto adicional.
"""
        
        return prompt
    
    def _process_gemini_response(self, response_text: str) -> GeminiAnalysis:
        """
        Processa a resposta do Gemini e converte para GeminiAnalysis.
        
        Args:
            response_text: Texto da resposta do Gemini
            
        Returns:
            GeminiAnalysis: Análise estruturada
        """
        try:
            # Tentar extrair JSON da resposta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                data = json.loads(json_text)
                
                return GeminiAnalysis(
                    success=True,
                    analysis=data.get('analysis', 'Análise não disponível'),
                    confidence=float(data.get('confidence', 0.5)),
                    recommendations=data.get('recommendations', []),
                    risk_assessment=data.get('risk_assessment', 'Médio'),
                    market_insights=data.get('market_insights', {})
                )
            else:
                # Se não conseguir extrair JSON, usar texto direto
                return GeminiAnalysis(
                    success=True,
                    analysis=response_text,
                    confidence=0.6,
                    recommendations=["Análise textual fornecida"],
                    risk_assessment="Médio",
                    market_insights={"raw_response": response_text}
                )
                
        except json.JSONDecodeError as e:
            return GeminiAnalysis(
                success=False,
                analysis="Erro ao processar resposta do Gemini",
                confidence=0.0,
                recommendations=[],
                risk_assessment="Alto",
                market_insights={},
                error_message=f"JSON inválido: {e}"
            )
        except Exception as e:
            return GeminiAnalysis(
                success=False,
                analysis="Erro inesperado na análise",
                confidence=0.0,
                recommendations=[],
                risk_assessment="Alto",
                market_insights={},
                error_message=str(e)
            )
    
    def _fallback_analysis(self, market_data: List[Dict], error_msg: str = None) -> GeminiAnalysis:
        """
        Análise de fallback quando Gemini não está disponível.
        
        Args:
            market_data: Dados dos mercados
            error_msg: Mensagem de erro opcional
            
        Returns:
            GeminiAnalysis: Análise básica local
        """
        # Análise básica local
        total_markets = len(market_data)
        has_live_markets = any(
            any(sel.get('name', '').lower() == 'type' and sel.get('odds') == 'live' 
                for sel in market.get('selections', []))
            for market in market_data
        )
        
        analysis = f"Análise local de {total_markets} mercados. "
        if has_live_markets:
            analysis += "Mercados ao vivo detectados - maior volatilidade esperada."
        else:
            analysis += "Mercados pré-jogo - análise baseada em dados estáticos."
        
        recommendations = [
            "Monitorar volumes de apostas",
            "Verificar movimentação de odds",
            "Considerar contexto do jogo"
        ]
        
        if error_msg:
            recommendations.append(f"Gemini indisponível: {error_msg}")
        
        return GeminiAnalysis(
            success=True,
            analysis=analysis,
            confidence=0.4,  # Confiança menor para análise local
            recommendations=recommendations,
            risk_assessment="Médio",
            market_insights={
                "total_markets": total_markets,
                "live_markets": has_live_markets,
                "analysis_type": "local_fallback"
            },
            error_message=error_msg
        )
    
    def format_analysis_result(self, analysis: GeminiAnalysis) -> str:
        """
        Formata o resultado da análise Gemini para exibição.
        
        Args:
            analysis: Resultado da análise
            
        Returns:
            str: Análise formatada
        """
        status_icon = "✅" if analysis.success else "❌"
        confidence_bar = "█" * int(analysis.confidence * 10) + "░" * (10 - int(analysis.confidence * 10))
        
        result = f"""
🧠 **ANÁLISE GEMINI AI** {status_icon}

📊 **Confiança:** {analysis.confidence:.1%} [{confidence_bar}]
🎯 **Risco:** {analysis.risk_assessment}

📝 **Análise:**
{analysis.analysis}

💡 **Recomendações:**
"""
        
        for i, rec in enumerate(analysis.recommendations, 1):
            result += f"{i}. {rec}\n"
        
        if analysis.market_insights:
            result += "\n🔍 **Insights dos Mercados:**\n"
            for key, value in analysis.market_insights.items():
                result += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        if analysis.error_message:
            result += f"\n⚠️ **Aviso:** {analysis.error_message}"
        
        return result

# Função principal para uso externo
def analyze_with_gemini(market_data: List[Dict], game_context: Dict = None) -> str:
    """
    Função principal para análise com Gemini.
    
    Args:
        market_data: Dados dos mercados
        game_context: Contexto do jogo
        
    Returns:
        str: Análise formatada
    """
    analyzer = GeminiAnalyzer()
    analysis = analyzer.analyze_betting_markets(market_data, game_context)
    return analyzer.format_analysis_result(analysis)

if __name__ == "__main__":
    # Teste da integração Gemini
    print("🧠 Testando integração com Gemini...")
    
    sample_data = [
        {
            "market_name": "Match Odds",
            "selections": [
                {"name": "Type", "odds": "live"},
                {"name": "Summ", "odds": "50000€"},
                {"name": "Odds", "odds": 2.1}
            ]
        }
    ]
    
    result = analyze_with_gemini(sample_data)
    print(result)