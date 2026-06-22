# 📊 Financial Analytics: Comportamento Transacional e Inteligência de Tempo

![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![DAX](https://img.shields.io/badge/DAX-Advanced-blue?style=for-the-badge)
![Data Modeling](https://img.shields.io/badge/Data_Modeling-Star_Schema-brightgreen?style=for-the-badge)

## 📌 Visão Executiva do Projeto
Este projeto é um **Dashboard Analítico Executivo** construído no Microsoft Power BI, focado na análise profunda do comportamento financeiro de clientes ao longo de 8 anos (2016 - 2024). 

Ao contrário de visões operacionais de curto prazo, este painel foi desenhado para responder a perguntas estratégicas de negócio: *Qual é a sazonalidade do nosso ecossistema? Como está o nosso crescimento Ano contra Ano (YoY)? Quem são os nossos clientes da Curva ABC?*

Os dados utilizados compreendem mais de 37.000 registros transacionais sintéticos de um *ledger* financeiro, englobando depósitos, saques, pagamentos e transferências.

---

## 🏗️ Arquitetura e Modelagem de Dados

O dataset original era composto por uma única tabela plana (*flat table*). Para garantir escalabilidade, performance do motor VertiPaq e precisão nas métricas de inteligência de tempo, o modelo foi reestruturado via **Power Query** para um **Star Schema** perfeito.

**Dimensões criadas:**
* `dCalendario`: Tabela de datas contínua gerada em DAX/M, essencial para as funções de *Time Intelligence*.
* `dContas`: Dimensão única de clientes (Account IDs).
* `dTipoTransacao`: Categorização do movimento financeiro (Deposit, Withdrawal, Transfer, Payment).

**Fato:**
* `fTransacoes`: Tabela transacional com granularidade diária, otimizada após a separação de *Timestamps* para reduzir a cardinalidade do modelo. Ocultação de chaves estrangeiras para forçar o uso correto das dimensões.

---

## 🧠 Motor de Cálculo (DAX Avançado)

O modelo conta com uma tabela dedicada (`_Medidas`) seguindo as melhores práticas de desenvolvimento. O destaque técnico vai para duas abordagens avançadas em DAX:

### 1. Inteligência de Tempo (Crescimento YoY)
Avaliação do crescimento do volume transacional em relação ao exato mesmo período do ano anterior.

```dax
Crescimento YoY % = 
VAR vVolumeAnoAnterior = CALCULATE([Volume Total], SAMEPERIODLASTYEAR(dCalendario[Data]))
RETURN
DIVIDE([Volume Total] - vVolumeAnoAnterior, vVolumeAnoAnterior, 0)
```

2. Medida Semi-Aditiva (Liquidez Real)
Como o saldo da conta não pode ser simplesmente somado ao longo dos dias, foi implementada uma iteração de contexto para buscar o último saldo válido de cada conta.

```Liquidez Disponivel = 
SUMX(
    VALUES(dContas[AccountID]),
    CALCULATE(
        LASTNONBLANKVALUE(dCalendario[Data], SUM(fTransacoes[AccountBalance]))
    )
)
```

🎨 Storytelling e Design Visual
O layout foi projetado baseando-se nos conceitos de Storytelling com Dados (Cole Nussbaumer Knaflic), utilizando o padrão de leitura em "Z" e a redução rigorosa de carga cognitiva (remoção de eixos desnecessários, uso intencional de cores).

A Bússola (Topo): KPIs diretos com formatação condicional (Volume Total, Crescimento YoY %, Ticket Médio, Taxa de Retenção de Capital).

A Visão Macro (Centro-Esquerda): Gráfico de Área demonstrando a evolução histórica de longo prazo e a tendência de adoção do ecossistema.

Comportamento & Sazonalidade (Centro-Direita): Matriz configurada como Heatmap (Mapa de Calor), evidenciando os dias e meses de maior estresse transacional.

Segmentação de Clientes (Rodapé): Gráfico de Barras horizontais filtrado para exibir o Top 10 Clientes (Curva ABC) baseando-se no volume movimentado.

💡 Insights Extraídos
Sazonalidade: Identificação clara de Payday Effects (dias de maior injeção de liquidez).

Fuga de Capital: Monitoramento da proporção entre o capital que entra (deposit) versus o que é drenado em operações físicas (withdrawal).

Concentração de Risco: Visibilidade imediata de quais AccountIDs representam a maior fatia do volume transacional da instituição.
