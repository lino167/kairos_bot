# 🎯 KAIROS - Estratégia de Dois Níveis

## 📋 Visão Geral

Implementação da estratégia inteligente de análise de mercados baseada na documentação do Excapper, otimizada para máxima eficiência e economia de recursos.

## 🏗️ Arquitetura

### Nível 1: Análise Preliminar (Filtro Rápido)
**Objetivo:** Identificar "sinais de fumaça" nos mercados
**Características:**
- ⚡ Rápida e barata
- 🔍 Baseada em regras claras
- 📊 Processa todos os mercados
- 🚨 Filtra apenas mercados com potencial

### Nível 2: Análise Profunda (IA Gemini)
**Objetivo:** Investigar se há "fogo" real nos mercados filtrados
**Características:**
- 🧠 Análise inteligente com IA
- 💰 Chamada apenas quando necessário
- 🎯 Foco nos mercados com sinais
- ✅ Decisão final de oportunidade

## 🔍 Sinais Detectados (Nível 1)

### 1. Money Way (Alto Volume)
**Descrição:** Detecta mercados com volume de dinheiro elevado

**Configurações:**
- Volume Mínimo: 5.000€ (Força: 0.6)
- Volume Alto: 15.000€ (Força: 0.8)
- Volume Muito Alto: 30.000€ (Força: 1.0)

**Exemplo:**
```python
# Volume de 25.000€ detectado
Signal: Money Way - Volume alto: 25000€ (>15000€)
Força: 0.8
```

### 2. Drop Odds (Queda de Odds)
**Descrição:** Identifica quedas significativas nas odds

**Configurações:**
- Queda Mínima: 5% (Força: 0.6)
- Queda Significativa: 10% (Força: 0.8)
- Queda Major: 20% (Força: 1.0)

**Exemplo:**
```python
# Queda de 12% detectada
Signal: Drop Odds - Queda significativa: -12% (>10%)
Força: 0.8
```

### 3. Sharp Bet (Dinheiro Súbito)
**Descrição:** Detecta movimentos súbitos de dinheiro em mercados ao vivo

**Configurações:**
- Volume Alto + Live: 10.000€ (Força: 0.7)
- Volume Muito Alto + Live: 20.000€ (Força: 0.9)

**Exemplo:**
```python
# Volume alto em mercado ao vivo
Signal: Sharp Bet - Possível sharp bet: 15000€ em mercado ao vivo
Força: 0.7
```

## 🚀 Como Usar

### Análise Completa (Recomendado)
```python
from modules.kairos_analyzer import analyze_betting_opportunity

# Dados dos mercados
market_data = [...]

# Análise de dois níveis
result = analyze_betting_opportunity(market_data)
print(result)
```

### Análise Programática
```python
from modules.kairos_analyzer import KairosAnalyzer

analyzer = KairosAnalyzer()
signals, opportunity = analyzer.analyze_markets_two_tier(market_data)

# Processar sinais
for signal in signals:
    print(f"Sinal: {signal.signal_type} - {signal.description}")

# Verificar oportunidade
if opportunity.found:
    print(f"Oportunidade: {opportunity.market} - {opportunity.selection}")
```

### Análise Apenas Preliminar
```python
from modules.kairos_analyzer import PreliminaryAnalyzer

analyzer = PreliminaryAnalyzer()
signals = analyzer.analyze_markets_preliminary(market_data)

print(f"Sinais detectados: {len(signals)}")
```

## 📊 Exemplo de Saída

```
🔍 **SINAIS DETECTADOS (Análise Preliminar):**
• Money Way (Alto Volume): 3 mercado(s)
• Drop Odds (Queda de Odds): 1 mercado(s)
• Sharp Bet (Dinheiro Súbito): 2 mercado(s)

🚨 **SINAIS FORTES:**
• Match Odds: Volume alto: 25000€ (>15000€)
• Match Odds: Queda significativa: -12.0% (>10%)
• Match Odds: Possível sharp bet: 25000€ em mercado ao vivo

🧠 **ANÁLISE PROFUNDA (IA):**
✅ **OPORTUNIDADE IDENTIFICADA**
• Mercado: Match Odds
• Seleção: Favorito identificado
• Confiança: Médio
• Justificativa: Match Odds: Volume moderado de 25000€...
```

## 💡 Vantagens da Estratégia

### ⚡ Eficiência
- Análise preliminar processa todos os mercados rapidamente
- IA é chamada apenas quando há potencial real
- Reduz custos de API significativamente

### 🎯 Precisão
- Filtro preliminar elimina ruído
- IA foca apenas em mercados promissores
- Combinação de regras + inteligência artificial

### 📈 Escalabilidade
- Pode processar centenas de mercados
- Tempo de resposta otimizado
- Uso inteligente de recursos

## 🔧 Configuração Avançada

### Ajustar Limites dos Sinais
```python
analyzer = PreliminaryAnalyzer()

# Personalizar configurações
analyzer.config['money_way']['min_volume'] = 8000  # Mais restritivo
analyzer.config['drop_odds']['min_drop_percent'] = 8  # Mais restritivo
```

### Filtrar por Força dos Sinais
```python
# Apenas sinais muito fortes (>= 0.8)
strong_signals = [s for s in signals if s.strength >= 0.8]
```

## 📚 Referências

- Documentação Excapper
- Estratégias de Trading Esportivo
- Análise de Volume e Movimento de Odds

---

**Desenvolvido para o KAIROS Bot** 🤖
*Análise inteligente de mercados de apostas*