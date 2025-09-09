# Kairos Bot 🤖⚽

Um sistema automatizado para análise e extração de oportunidades de apostas esportivas do site Excapper.

## 📋 Funcionalidades

- **Extração de dados em tempo real** de jogos ao vivo
- **Análise de oportunidades** baseada em volume de apostas
- **Estrutura modular** para fácil manutenção e extensão
- **Sistema de logs** para monitoramento
- **Extração de links** para páginas individuais de jogos

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd kairos_bot
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale o Playwright:
```bash
playwright install
```

## 📁 Estrutura do Projeto

```
kairos_bot/
├── venv/                    # Ambiente virtual Python
├── investigate_html.py      # Script de investigação HTML
├── requirements.txt         # Dependências do projeto
├── analysis_report.json     # Relatório detalhado da análise
├── sample_page.html         # Amostra do HTML capturado
└── README.md               # Este arquivo
```

## 🔍 Descobertas da Investigação

### Estrutura do Site
- **Título**: "Drop odds on bet exchange. Money way on betfair"
- **Tabelas principais**: 4 tabelas identificadas
- **Tabela principal**: 101 linhas com colunas: Data, Country, League, Teams, All money

### Dados Extraíveis Identificados

#### 📅 Datas dos Jogos
- **Elementos encontrados**: 108
- **Formato**: DD.MM.YYYY HH:MM
- **Exemplo**: "09.09.2025 11:00"

#### 💰 Valores Monetários
- **Elementos encontrados**: 107
- **Formato**: Valores em euros (€)
- **Exemplos**: "3789 €", "9325 €", "708 €"

#### ⚽ Times e Competições
- **Elementos encontrados**: 142
- **Tipos identificados**:
  - Jogos internacionais U19, U21, U23
  - Ligas profissionais inglesas
  - Eliminatórias da Copa do Mundo FIFA
  - Copas nacionais

### Exemplos de Dados Encontrados

#### Times e Competições:
- Spain U19 - Ukraine U19
- Colchester United U21 - Fleetwood Town U21
- English U21 Pro Development League
- FIFA World Cup Qualifiers - Africa

#### Estrutura das Tabelas:
1. **Tabela Principal** (101 linhas)
   - Data
   - Country
   - League
   - Teams
   - All money

2. **Tabelas Secundárias** (6-7 linhas cada)
   - Mesma estrutura da principal

## 🛠️ Configuração do Ambiente

### 1. Ativar Ambiente Virtual
```bash
venv\Scripts\activate
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar Investigação
```bash
python investigate_html.py
```

## 📦 Dependências

- **requests**: Para fazer requisições HTTP
- **beautifulsoup4**: Para parsing HTML
- **lxml**: Parser XML/HTML rápido
- **selenium**: Para automação de navegador (se necessário)
- **pandas**: Para manipulação de dados
- **openpyxl**: Para exportar dados para Excel

## 🎯 Próximos Passos

1. **Criar scraper específico** para extrair dados das tabelas
2. **Implementar sistema de monitoramento** para mudanças nos dados
3. **Adicionar exportação** para CSV/Excel
4. **Implementar sistema de notificações** para alertas
5. **Criar dashboard** para visualização dos dados

## 📊 Dados Técnicos

- **User-Agent**: Configurado para simular navegador real
- **Headers HTTP**: Configurados para evitar bloqueios
- **Timeout**: 10 segundos por requisição
- **Encoding**: UTF-8 para suporte a caracteres especiais

## ⚠️ Considerações Importantes

- Respeitar robots.txt do site
- Implementar delays entre requisições
- Monitorar mudanças na estrutura HTML
- Considerar aspectos legais do web scraping

## 📈 Potencial de Dados

O site contém informações valiosas sobre:
- Odds de apostas em tempo real
- Movimentação de dinheiro nas casas de apostas
- Calendário de jogos esportivos
- Estatísticas de diferentes competições

---

**Desenvolvido por**: Kairos Bot Team  
**Data**: Setembro 2025  
**Versão**: 1.0.0