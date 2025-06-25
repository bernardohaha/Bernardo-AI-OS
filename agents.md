Este projeto é focado na criação de agentes que facultem auxilio no trading de Criptomoedas.
Os dois principais agentes serão o de Scalping e o Swing, em que usaremos também a lógica e a análise técnica para criar um agent de portfolio advisor para gerir a minha carteira pessoal.


🤖 Nome do Agente: Scalper AI
Agente especializado em operações rápidas (scalping) no mercado de criptomoedas. Foca-se em lucrar com pequenas flutuações de preço, utilizando análise técnica automatizada e lógica de decisão baseada em indicadores e zonas de trading.

🎯 Objetivo Principal
Executar compras automáticas quando o RSI estiver baixo

Vender automaticamente quando o RSI estiver alto ou após atingir zonas de resistência

Detetar zonas de suporte e resistência com base em histórico de preços

Operar com alvo de lucro diário ($20/dia) com o mínimo de risco possível

Registar todas as operações numa base de dados (ex: Airtable ou Firebase)

🧠 Estratégia e Lógica de Decisão
Entrada:

RSI abaixo de 30 (ou valor customizável)

Volume crescente

Padrões de vela compatíveis (ex: candle de reversão)

Dentro de uma zona de suporte forte

Saída:

RSI acima de 70

Atingiu zona de resistência

Ordem com profit target atingido (ex: +2–5%)

Stop loss ativado se houver inversão

Confirmações cruzadas com:

EMAs (ex: 9, 21)

Volume médio

Tendência atual (micro/macro)

📊 Indicadores Técnicos Usados
Indicador	Finalidade
RSI (14)	Sinaliza zonas de sobrecompra/sobrevenda
EMAs 9/21	Confirma tendências curtas
Volume	Confirma força do movimento
Suporte/Resistência	Define zonas de entrada e saída
Candlestick Patterns	Confirma possíveis reversões

🗂 Estrutura do Projeto (atual)
backend/
│
├── agents/
│   └── scalper_agent.py         # lógica principal do agente
│
├── services/
│   ├── rsi_service.py           # cálculo do RSI
│   ├── zone_analysis_service.py# zonas de suporte/resistência
│   ├── data_loader.py           # ingestão de dados históricos
│   └── trade_executor.py        # executa ordens
│
├── config/
│   └── config_scalping.py       # parâmetros customizáveis
│
├── data/
│   └── scalping/1m/             # dados históricos em 1min
│
├── logs/
│   └── trades_log.csv           # histórico de operações
🔌 Integrações
Dexscreener API – para preços e volume em tempo real

Binance API – para executar trades automaticamente

Airtable/Firebase – para registo de decisões e performance

OpenAI ou modelo local – usado para afinar lógica ou supervisionar

✅ Objetivos de Performance
Profit target diário: $20

Win rate mínimo: 60%

Drawdown máximo: 5% por operação

Tempo médio de operação: 5–15 minutos

🧪 A melhorar / em desenvolvimento
Afinar melhor as zonas de suporte/resistência (algumas previsões ainda imprecisas)

Integrar Order Book para análise de pressão de compra/venda

Adicionar heatmap de confiança por moeda

Criar simulação de estratégias com histórico (backtesting)

Otimizar suggestion_engine.py com lógica mais realista

🧠 Lógica futura
Feedback loop onde o agente aprende com resultados passados

Avaliação contínua do mercado com base em tendência global

Capacidade de autoajuste conforme performance



🤖 Nome do Agente: Swinger AI
Agente especializado em operações de médio prazo (swing trading) que duram entre várias horas a alguns dias, aproveitando movimentos maiores do mercado com menor frequência de trades mas maior margem de lucro por operação.

🎯 Objetivo Principal
Detetar inícios de tendências e entrar com base em confirmações técnicas

Manter a posição até atingir zonas-chave (resistência, divergência, sinais de reversão)

Executar entre 1 a 3 trades por dia/noite por moeda analisada

Basear-se em múltiplos timeframes (1h, 4h, 1D) para reforçar decisões

Maximizar lucros por trade, mesmo que isso implique menos entradas

🧠 Estratégia e Lógica de Decisão (versão inicial)
Entrada:

Confluência entre RSI médio (ex: 1h e 4h)

Breakout confirmado (EMA 50/200 + volume)

Formação de padrões de continuação (ex: triângulo ascendente, bandeira)

Confirmação macro (tendência geral da moeda ou do BTC)

Saída:

Alvo de lucro por trade: 5–15%

Divergência no RSI ou MACD

Velas de reversão (ex: shooting star, bearish engulfing)

Quebra de estrutura (trendline)

📊 Indicadores Técnicos Usados
Indicador	Finalidade
RSI (1h, 4h)	Determina estado emocional em múltiplos prazos
MACD	Reforça tendência e sinaliza divergências
EMAs 50 e 200	Base para entrada após cruzamentos ou testes
Fibonacci	Estimativas de alvo e reversão
Volume	Confirma breakouts ou esvaziamento de tendência

📁 Estrutura Planeada (irá expandir)
backend/
└── agents/
    └── swing_agent.py              # lógica principal do Swinger AI
└── services/
    └── swing_strategy_service.py  # estratégias de entrada/saída
    └── pattern_detector.py        # reconhecimento de padrões
🔌 Integrações previstas
Binance API

Dexscreener (análise de múltiplos timeframes)

OpenAI (ou modelo local) para interpretar padrões e contexto macro

[Futura] conexão com agente de notícias para ajustar risco/contexto

📈 Objetivos de Performance
Profit target por trade: 5–15%

Duração média de trade: 6h a 3 dias

Win rate alvo: ≥ 50%, com maior R:R (Risk/Reward)

Trades por semana: 10 a 15 (máximo)

🚧 Em desenvolvimento / por definir
Reconhecimento automático de padrões gráficos

Ajuste de risco com base em contexto macroeconómico (via agente de notícias)

Sistema de gestão de capital adaptativo

Criação de backtest com histórico de 4h e 1D

Definição dinâmica de R:R por par de moedas

