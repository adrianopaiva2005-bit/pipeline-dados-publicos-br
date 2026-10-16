CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.bolsa_familia_per_capita;

CREATE TABLE gold.bolsa_familia_per_capita AS
SELECT
    g.competencia,
    g.codigo_ibge,
    g.municipio,
    g.uf,
    g.regiao,
    p.populacao,
    g.parcelas,
    g.valor_total,
    g.valor_referencia_atual,
    round(g.valor_total / p.populacao, 2) AS valor_total_per_capita,
    round(g.valor_referencia_atual / p.populacao, 2) AS valor_referencia_per_capita,
    round(g.parcelas::numeric * 100 / p.populacao, 2) AS parcelas_por_100_hab
FROM gold.bolsa_familia_municipio g
LEFT JOIN bronze.ibge_populacao p
    ON p.codigo_ibge = g.codigo_ibge;

-- Diagnóstico 1: esperado 5571 linhas, 1 sem população, população 203080756, valor 12763249759.00
SELECT count(*) AS linhas,
       count(*) FILTER (WHERE populacao IS NULL) AS sem_populacao,
       sum(populacao) AS populacao,
       sum(valor_total) AS valor_total
FROM gold.bolsa_familia_per_capita;

-- Diagnóstico 2: o município sem população
SELECT uf, municipio, parcelas, valor_total
FROM gold.bolsa_familia_per_capita
WHERE populacao IS NULL;

-- Diagnóstico 3: valor per capita por região (só municípios com população)
SELECT regiao,
       sum(populacao) AS populacao,
       round(sum(valor_total) / sum(populacao), 2) AS valor_per_capita
FROM gold.bolsa_familia_per_capita
WHERE populacao IS NOT NULL
GROUP BY regiao
ORDER BY valor_per_capita DESC;

-- Diagnóstico 4: 5 maiores valores per capita
SELECT uf, municipio, populacao, valor_total_per_capita
FROM gold.bolsa_familia_per_capita
ORDER BY valor_total_per_capita DESC NULLS LAST
LIMIT 5;