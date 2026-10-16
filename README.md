# pipeline-dados-publicos-br

Pipeline de dados com dados abertos brasileiros: ingestão, camadas bronze/silver/gold em PostgreSQL e análise do Bolsa Família por município.

## Fontes

- IBGE, API de localidades: cadastro de 5.571 municípios.
- Portal da Transparência: Novo Bolsa Família, competência 202608 (CSV de 1,9 GB, 18.809.420 linhas).
- IBGE, SIDRA tabela 4709: população do Censo 2022 por município.

Os dados brutos ficam em `data/`, fora do Git. O CSV do Portal contém dados pessoais (CPF, NIS e nomes). O pipeline lê o arquivo em fluxo e agrega por município sem acessar esses campos. Nada pessoal é gravado no banco nem versionado.

## Camadas

- bronze: `ibge_municipios`, `portal_bolsa_familia` (14.694 grupos agregados), `ibge_populacao` (5.570 municípios).
- silver: `ibge_municipios` e `portal_bolsa_familia`, esta cruzada com o IBGE pelo código SIAFI, com 32 exceções manuais.
- gold: `bolsa_familia_municipio` (5.571 linhas) e `bolsa_familia_per_capita`.

## Validações

O total de R$ 12.763.249.759,00 e as 18.809.420 parcelas foram conferidos em todas as camadas, sem perda nem duplicação no cruzamento com o IBGE.

## Resultados (competência 202608)

O Nordeste concentra cerca de 46% do valor (R$ 5,93 bilhões). Em valor per capita, Nordeste (R$ 108,42) e Norte (R$ 99,20) ficam acima de Centro-Oeste (R$ 42,48), Sudeste (R$ 42,03) e Sul (R$ 28,65). Em valor absoluto, os maiores municípios são São Paulo, Rio de Janeiro, Salvador, Fortaleza e Manaus. Em per capita, aparecem municípios pequenos do Norte e do Nordeste, como Itaubal (AP), Autazes (AM) e Cachoeira Grande (MA).

## Limitações

- Boa Esperança do Norte (MT) não tem população na tabela do Censo usada e fica sem valor per capita. Recebeu R$ 78.936,00, cerca de 0,0006% do total.
- A população é de 2022 e os pagamentos são de 2026.
- Os municípios com maior per capita têm de 37 a 38 parcelas por 100 habitantes no pipeline, contra 9,26 no Brasil. O painel VIS Data do MDS, consultado para os cinco primeiros do ranking (agosto de 2026), registra de 36 a 39 famílias por 100 habitantes, então o padrão aparece nas duas fontes. Os números diferem de município para município, conforme a tabela abaixo, e a causa dessas diferenças não foi verificada. Os valores do painel foram lidos de capturas de tela.
- A análise cobre uma única competência, não é série histórica.

Comparação em agosto de 2026 entre o pipeline e o painel VIS Data. As porcentagens são calculadas sobre o valor do pipeline, e o sinal indica como o painel fica em relação a ele.

| Município | Parcelas (pipeline) | Famílias (VIS Data) | Diferença na contagem | Valor (pipeline) | Valor (VIS Data) | Diferença no valor |
|---|---|---|---|---|---|---|
| Itaubal (AP) | 2.074 | 2.024 | −2,4% | R$ 1.523.977,00 | R$ 1.537.777,00 | +0,9% |
| Autazes (AM) | 15.716 | 15.932 | +1,4% | R$ 10.921.755,00 | R$ 11.084.267,00 | +1,5% |
| Cachoeira Grande (MA) | 3.623 | 3.653 | +0,8% | R$ 2.514.014,00 | R$ 2.539.489,00 | +1,0% |
| Serrano do Maranhão (MA) | 3.813 | 4.011 | +5,2% | R$ 2.618.406,00 | R$ 2.745.766,00 | +4,9% |
| Rodelas (BA) | 3.885 | 3.922 | +1,0% | R$ 2.621.540,00 | R$ 2.650.190,00 | +1,1% |

## Comparação com a referência atual

A primeira tabela compara o VIS Data com o total do pipeline, que inclui as parcelas com mês de referência anterior à competência (chamadas aqui de retroativas; o dicionário do Portal não usa esse termo). A tabela abaixo usa só as parcelas com as duas colunas iguais (`referencia = competencia`) em agosto de 2026. As porcentagens usam o valor do pipeline como base, e o sinal indica a diferença do VIS Data em relação a ele.

| Município | Parcelas, ref. atual (= NIS distintos) | Famílias (VIS Data) | Diferença na contagem |
|---|---|---|---|
| Itaubal (AP) | 2.003 | 2.024 | +1,0% |
| Autazes (AM) | 15.672 | 15.932 | +1,7% |
| Cachoeira Grande (MA) | 3.610 | 3.653 | +1,2% |
| Serrano do Maranhão (MA) | 3.802 | 4.011 | +5,5% |
| Rodelas (BA) | 3.875 | 3.922 | +1,2% |

Com a referência atual, o VIS Data fica acima do pipeline nos cinco municípios, tanto na contagem quanto no valor. Em Itaubal, a diferença de valor (+4,1%) é maior que a de contagem (+1,0%), e isso não foi explicado.

No CSV, `MÊS COMPETÊNCIA` é 202608 em todas as linhas e `MÊS REFERÊNCIA` varia de 202601 a 202608. As linhas com as duas colunas iguais são 18.778.626 (99,84%). A descrição das colunas no dicionário de dados do Portal (competência como o mês a que a parcela se refere, referência como o mês da folha de pagamento) não esclarece por que há referências anteriores à competência, então o sentido exato delas não foi confirmado. O dicionário também lista a coluna `DATA DISPONIBILIZAÇÃO`, que não existe no arquivo local (data de modificação: 24/09/2026).

O que foi verificado: cada linha do CSV do Portal é um pagamento individual (há colunas de favorecido e valor da parcela, mas nenhuma de família ou domicílio), então a coluna `parcelas` do pipeline conta pagamentos. Nos cinco municípios, o número de NIS distintos é igual ao número de linhas da referência atual, nenhum NIS aparece mais de uma vez nessa referência, e os retroativos não acrescentam NIS novos. Essa checagem foi feita apenas nesses cinco municípios, não no Brasil inteiro.

O que o MDS declara: a ficha do indicador IN001 (SAGICAD, editada em 29/09/2026), para a qual o ícone de informação do VIS Data aponta, define a unidade estatística como família e o cálculo como "contagem distinta de famílias beneficiárias do Programa Bolsa Família constantes em folha de pagamento do período de referência". A fonte é a folha de pagamento operacionalizada pela Caixa, junto com o Cadastro Único. A ficha prevê revisão retroativa dos valores. No total nacional de agosto de 2026, o painel registra 19.289.215 famílias e R$ 13.056.767.658,00, contra 18.809.420 parcelas e R$ 12.763.249.759,00 no pipeline (+2,6% e +2,3%).

O que não foi verificado: a causa da diferença com o painel. A ficha não diz como a família é identificada na folha (o CSV do Portal não tem coluna de família), como trata parcelas com referência anterior à competência, nem se o Portal e o painel usam a mesma extração. Os valores municipais do VIS Data vêm de capturas de tela, e o arquivo local tem data de modificação de 24/09/2026. Como a ficha admite revisões retroativas, as duas bases podem ser de momentos diferentes, mas isso não foi confirmado.

## Como executar

O projeto usa Python 3.14, fixado em `.python-version`. O pipeline completo roda com um único comando, que executa ingestão, carga bronze, silver, gold e os testes de qualidade, parando no primeiro erro:

    uv run python src/pipeline/run_pipeline.py

Para pular a ingestão e reaproveitar os arquivos já gerados em `data/` (sem consultar as APIs do IBGE de novo e sem reler o CSV do Portal, de cerca de 2 GB, que precisa ser baixado manualmente):

    uv run python src/pipeline/run_pipeline.py --pular-ingestao

A opção `--sem-testes` omite o pytest no final. As cargas são idempotentes: cada `load_*` limpa os dados que vai recarregar e cada SQL recria suas tabelas, então o pipeline pode ser executado várias vezes sem duplicar valores.

Em 16/10/2026, o pipeline completo (sem `--pular-ingestao`) foi executado com sucesso em 48,9 s: 18.809.420 linhas lidas, 14.694 grupos, R$ 12.763.249.759,00 e os cinco testes aprovados. A ingestão do IBGE e da população baixa os dados das APIs, mas a etapa do Portal não faz download: ela lê o arquivo `data/bronze/portal_transparencia/202608_NovoBolsaFamilia.csv`, que precisa ser baixado do Portal da Transparência (Download de dados, Novo Bolsa Família, competência 202608) e colocado nessa pasta antes da execução. Se o arquivo não existir, o pipeline para nessa etapa com uma mensagem indicando o que fazer, comportamento testado na mesma data.

## Dashboard

O dashboard em Streamlit lê somente `gold.bolsa_familia_per_capita` e tem três abas: Regiões (valor total e per capita por região), Ranking (municípios ordenados por valor per capita, valor total ou parcelas por 100 habitantes, com filtro de população mínima) e Municípios (busca por nome e filtro por UF). Os totais do topo conferem com o pipeline: R$ 12.763.249.759,00, 18.809.420 parcelas, 5.571 municípios e 203.080.756 habitantes.

Com o PostgreSQL rodando e o pipeline já executado, inicie o app com `uv run streamlit run dashboard/app.py`.

O app abre em `http://localhost:8501`. As credenciais vêm do `.env`. Nas ordenações por valor per capita e por parcelas por 100 habitantes, o dashboard exibe um aviso de cautela sobre a cobertura alta dos municípios pequenos. Na aba Municípios, os valores aparecem com ponto decimal e sem separador de milhar, porque o `st.column_config` não aceita formato de localidade; os números do topo seguem o padrão brasileiro.

## Testes

Os testes de qualidade (`uv run pytest -v`) verificam, nas tabelas gold, o número de linhas, os totais de valor, parcelas e população, a única exceção sem população (Boa Esperança do Norte) e o teto de cobertura de 40 parcelas por 100 habitantes. Dependem do PostgreSQL local com os dados da competência 202608, então não rodam em CI.

## Próximos passos

- Procurar documentação que explique como a família é identificada na folha de pagamento e se a base do Portal é a mesma do painel. A ficha IN001 define o indicador, mas não explica a diferença observada.
- Avaliar o per capita pela referência atual em vez do total de parcelas e verificar se o ranking dos cinco maiores muda.