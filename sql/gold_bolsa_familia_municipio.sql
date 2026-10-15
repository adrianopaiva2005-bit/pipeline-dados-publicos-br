CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.bolsa_familia_municipio;

CREATE TABLE gold.bolsa_familia_municipio AS
SELECT
    p.competencia,
    p.codigo_ibge,
    i.nome AS municipio,
    i.uf_sigla AS uf,
    i.regiao_nome AS regiao,
    sum(p.parcelas) AS parcelas,
    sum(p.valor_total) AS valor_total,
    round(sum(p.valor_total) / sum(p.parcelas), 2) AS valor_medio_parcela,
    coalesce(sum(p.valor_total) FILTER (WHERE p.referencia = p.competencia), 0)
        AS valor_referencia_atual
FROM silver.portal_bolsa_familia p
JOIN silver.ibge_municipios i
    ON i.codigo_ibge = p.codigo_ibge
GROUP BY p.competencia, p.codigo_ibge, i.nome, i.uf_sigla, i.regiao_nome;

-- Diagnóstico 1: esperado 5571 linhas e valor_total 12763249759.00
SELECT count(*) AS linhas, sum(valor_total) AS valor_total
FROM gold.bolsa_familia_municipio;

-- Diagnóstico 2: valor total por região
SELECT regiao, count(*) AS municipios, sum(parcelas) AS parcelas, sum(valor_total) AS valor_total
FROM gold.bolsa_familia_municipio
GROUP BY regiao
ORDER BY valor_total DESC;

-- Diagnóstico 3: 5 municípios com maior valor total
SELECT uf, municipio, parcelas, valor_total
FROM gold.bolsa_familia_municipio
ORDER BY valor_total DESC
LIMIT 5;