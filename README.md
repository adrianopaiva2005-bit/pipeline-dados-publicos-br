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
- Os municípios com maior per capita têm de 37 a 38 parcelas por 100 habitantes, contra 9,26 no Brasil. Esse número ainda não foi confrontado com uma fonte oficial (famílias beneficiárias no painel do MDS) e deve ser lido com cautela.
- A análise cobre uma única competência, não é série histórica.

## Como executar

O pipeline completo roda com um único comando, que executa ingestão, carga bronze, silver, gold e os testes de qualidade, parando no primeiro erro:

    uv run python src/pipeline/run_pipeline.py

Para reaproveitar os arquivos já baixados em `data/` (útil porque o CSV do Portal tem cerca de 2 GB):

    uv run python src/pipeline/run_pipeline.py --pular-ingestao

A opção `--sem-testes` omite o pytest no final. As cargas são idempotentes: cada `load_*` limpa os dados que vai recarregar e cada SQL recria suas tabelas, então o pipeline pode ser executado várias vezes sem duplicar valores.

## Testes

Os testes de qualidade (`uv run pytest -v`) verificam, nas tabelas gold, o número de linhas, os totais de valor, parcelas e população, a única exceção sem população (Boa Esperança do Norte) e o teto de cobertura de 40 parcelas por 100 habitantes. Dependem do PostgreSQL local com os dados da competência 202608, então não rodam em CI.

## Próximos passos

- Confrontar a cobertura dos municípios com maior per capita com o número de famílias do painel do MDS.
- Orquestrar o pipeline de ponta a ponta.
- Construir um dashboard com os resultados.