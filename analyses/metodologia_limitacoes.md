# Metodologia, rastreabilidade e limites dos experimentos

Este documento complementa os [quatro relatórios](../README.md#análises) e os quatro notebooks do projeto **Financial Transaction Intelligence**. Descreve o que foi efetivamente executado no Colab, o que foi deduzido das saídas e o que ainda exige investigação. **Não** apresenta certificação de modelos para uso real em instituições financeiras.

## Fontes e separação das bases

| Fonte | Abrangência | Uso | Cuidados |
|---|---|---|---|
| [Banking Transactions 2019–2024](https://www.kaggle.com/datasets/belbino/indian-banking-transactions-20192024) | 550.000 registros originais; 505.980 transações válidas no período 2019–2023 após filtros | ABC, HHI, Gini, clusters, forecasting, entradas e saídas | Montantes denominados em **INR**; o arquivo inclui janeiro/2024 incompleto |
| [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) | 6.362.620 operações sintéticas distribuídas em 743 etapas horárias; 8.213 fraudes simuladas | Classificação e análise de fraude | Valores em **unidade simulada**, relógio fictício e regras próprias de geração dos rótulos |

**Não existe uma chave confiável de cliente, instituição, calendário ou moeda entre esses arquivos.** O projeto não realiza `JOIN` de clientes nem soma valores financeiros dos dois datasets. O termo “inteligência financeira integrada” refere-se às análises em um mesmo portfólio, **não a um livro-razão único**.

## Procedimento de aquisição e limpeza

Os notebooks podem baixar os CSVs diretamente do Kaggle no Google Colab com `kagglehub`, sem armazenar arquivos grandes no repositório. Cada notebook configura o caminho de entrada por variável de ambiente; dados locais podem ser usados fora do Colab. A célula inicial valida a existência do CSV e as colunas exigidas; **validar cabeçalho não equivale a auditar a integridade de todas as linhas**.

No Banking, as etapas de preparação incluem:

1. Leitura apenas das colunas necessárias.
2. Conversão de data e valor financeiro.
3. Remoção de IDs de transação duplicados e registros inválidos conforme a lógica do notebook.
4. Inclusão apenas de `transaction_status = Success` e `transaction_amount >= 0`.
5. Exclusão de bordas mensais incompletas e, para comparações anuais, exigência de **12 meses** por ano.

O log da execução analisada mostrou **267 transações removidas de janeiro de 2024**, restando 2019–2023. Do total original de 550.000 registros, 505.980 permaneceram no recorte válido; uma auditoria do **motivo individual de cada exclusão** ainda seria necessária para reconciliar todas as diferenças sem inferências.

No PaySim, o notebook usa somente `step`, `type`, `amount`, `isFraud` e `isFlaggedFraud` na leitura, além de verificações básicas de valores válidos. **`isFlaggedFraud` é usado para comparação, não como feature de treinamento.**

## Descrição das quatro etapas

| Notebook | Técnicas | Validação realizada | Limitação principal |
|---|---|---|---|
| [01 — Concentração e clientes](../notebooks/01_concentracao_abc_clustering.ipynb) | ABC, HHI, Gini, RobustScaler, K-Means | Indicadores anuais calculados sobre 2019–2023 e tabelas de clusters executadas | Estabilidade do clustering e qualidade dos agrupamentos não totalmente quantificadas |
| [02 — Forecast segmentado](../notebooks/02_forecast_segmentos.ipynb) | Naive sazonal, ARIMA, SARIMA, XGBoost | Duas origens cronológicas; seis previsões por modelo e segmento no modo rápido | SARIMA total instável; poucos segmentos/janelas |
| [03 — Fraudes](../notebooks/03_fraudes_picos_movimentacao.ipynb) | Random Forest, XGBoost, F2, AP, SHAP, validação cronológica | Treino/validação/teste separados por etapa; avaliação de subgrupos | O modelo final foi escolhido pelo teste, exigindo correção metodológica |
| [04 — Fluxo e anomalias](../notebooks/04_fluxo_previsao_anomalias.ipynb) | SARIMA, XGBoost, Naive sazonal, Isolation Forest | Série mensal de 60 meses; validação por origens, alertas em janela posterior | Instabilidade do SARIMA em débitos e ausência de rótulos de anomalia |

As métricas dos relatórios foram **transcritas de saídas reais dos notebooks executados pelo usuário no Colab**, compartilhadas nesta conversa. O arquivo [`assets/data/metricas_colab.json`](../assets/data/metricas_colab.json) conserva os indicadores resumidos usados para construir as figuras. **Essa reprodução não significa uma execução independente por este projeto ou uma auditoria do CSV completo neste commit.**

Os gráficos da pasta `assets/images/` são **SVGs estáticos reconstruídos desses valores**, e não capturas exportadas diretamente dos notebooks. Quando as tabelas originais exibem notação científica arredondada, os gráficos correspondentes também são aproximados e identificados como tais.

## Fórmulas e conceitos

- **HHI de participação transacional:** `10.000 × Σ(participação_do_cliente²)`. Não utilizar como índice de competição de mercado.
- **Curva ABC:** ordenação por valor movimentado por cliente, com classificação com base no acumulado de 80%, 95% e 100% (limiares convencionais).
- **Gini:** medida de desigualdade de valores movimentados, não de renda ou patrimônio dos clientes.
- **MAE:** média dos valores absolutos dos erros.
- **WAPE:** soma dos erros absolutos dividida pela soma dos valores efetivamente observados, sujeito a distorções quando o denominador é muito pequeno.
- **Average Precision:** qualidade da ordenação de scores para classe rara; **não** é precisão calculada em um limiar fixo.
- **Recall:** fraudes identificadas entre as fraudes existentes.
- **SHAP:** contribuição atribuída às variáveis nas saídas do modelo; não implica causalidade.

## Prevenção de vazamento de informação

**Forecast:** seleção de segmentos, construção das séries, treinamento de modelos e projeção recursiva devem operar apenas com as observações que precedem cada origem de validação. Dados de 2024 incompletos foram excluídos. O baseline sazonal foi ajustado para comparar **meses correspondentes** do ano anterior.

**Fraude:** transações são divididas cronologicamente por `step`. A feature `horario_pico` foi calculada com informações da janela de treino. Os saldos de origem e destino (`oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`) não entraram no treinamento por limitações de sua semântica no PaySim. `isFraud` é **rótulo**, não feature. Os resultados de classificação ainda sofrem de **seleção do modelo pelo AP do teste**; o procedimento precisa passar a usar a validação para essa escolha.

**Clustering:** o agrupamento é descritivo, calculado com a amostra histórica agregada e não usado como previsão temporal. Para aplicação prospectiva, transformações e clusters devem ser ajustados somente ao histórico disponível na data de predição.

**Anomalias:** o Isolation Forest é treinado na janela anterior à avaliação, mas o número limitado de meses e a ausência de rótulos impedem validação supervisionada de alertas.

## Resultados preliminares e interpretação

- Concentração: o Top 1% movimentou de 25,28% a 27,58% nos anos completos; Gini aproximadamente 0,84.
- Forecast TOTAL: Naive sazonal com WAPE **4,94%** na validação apresentada; SARIMA extremamente instável em uma janela.
- PaySim: XGBoost com **AP 0,358** e **recall 51,39%** no teste cronológico; variação de prevalência de 0,0833% para 1,3384% entre treino e teste.
- Fluxos: os débitos excederam créditos na maior parte dos meses, mas isso **não** representa prejuízo; o Isolation Forest sinalizou dois meses após o corte de calibração.

## Verificações pendentes antes de afirmar robustez

1. Registrar contagens e motivos de exclusão etapa a etapa em Banking, com checagem de tipos, duplicados e datas.
2. Ampliar as origens de forecast e comparar erros por mês, horizonte e segmento; verificar convergência do SARIMA, escala e estabilidade entre janelas.
3. Fixar a seleção do modelo antifraude pela validação, recalibrar limiares e avaliar custo de falso negativo/falso positivo sem usar o conjunto de teste na escolha.
4. Relatar Silhouette Score, distribuição de variáveis e estabilidade dos clusters em amostras temporais ou reamostragens.
5. Comparar Isolation Forest a referências simples de anomalia sazonal e evitar chamar um outlier de fraude.
6. Regenerar as figuras diretamente das saídas dos notebooks, com validação de medidas e unidades.

## Executar os notebooks

Os notebooks contêm **um único título Markdown inicial e depois somente células de código**. Abra os arquivos da pasta [`notebooks/`](../notebooks/) em ambiente Python compatível ou no Colab, permita a instalação de dependências e execute todas as células. `FINANCE_BI_FAST_TEST=1` reduz o custo dos modelos, **não** implica execução sobre uma amostra idêntica em todos os experimentos. Para análise completa, use `FINANCE_BI_FAST_TEST=0` e confira recursos, tempo e mensagens de convergência.

**Não executar o mesmo arquivo duas vezes como se fosse um segundo conjunto de observações.** As bases são independentes e os resultados não devem ser combinados em uma métrica financeira única.

---

**Proveniência editorial:** relatórios e imagens baseados nas saídas fornecidas em 09/11/2026. Nenhuma cifra deve ser interpretada como auditoria financeira, rendimento real, previsão operacional atual ou desempenho pronto para produção.
