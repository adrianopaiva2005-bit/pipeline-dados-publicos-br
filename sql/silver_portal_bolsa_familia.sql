CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE FUNCTION silver.normaliza_nome(texto text)
RETURNS text AS $$
    SELECT trim(regexp_replace(upper(unaccent(texto)), '[^A-Z0-9]+', ' ', 'g'))
$$ LANGUAGE sql STABLE;

DROP TABLE IF EXISTS silver.portal_bolsa_familia;
DROP TABLE IF EXISTS silver.siafi_ibge;

CREATE TABLE silver.siafi_ibge AS
SELECT
    p.uf,
    p.codigo_siafi,
    p.municipio AS municipio_portal,
    i.codigo_ibge,
    i.nome AS nome_ibge
FROM (
    SELECT DISTINCT uf, codigo_siafi, municipio
    FROM bronze.portal_bolsa_familia
) p
LEFT JOIN silver.ibge_municipios i
    ON i.uf_sigla = p.uf
   AND silver.normaliza_nome(i.nome) = silver.normaliza_nome(p.municipio);

CREATE TABLE silver.portal_bolsa_familia AS
SELECT
    b.competencia,
    b.referencia,
    b.uf,
    b.codigo_siafi,
    s.codigo_ibge,
    b.municipio AS municipio_portal,
    b.parcelas,
    b.valor_total
FROM bronze.portal_bolsa_familia b
JOIN silver.siafi_ibge s
    ON s.uf = b.uf
   AND s.codigo_siafi = b.codigo_siafi
   AND s.municipio_portal = b.municipio;

-- Diagnóstico 1: deve dar 14694 linhas, 18809420 parcelas e 12763249759.00
SELECT count(*) AS linhas, sum(parcelas) AS parcelas, sum(valor_total) AS valor_total
FROM silver.portal_bolsa_familia;

-- Diagnóstico 2: municípios do Portal, quantos sem correspondência e IBGE repetidos
SELECT
    count(*) AS municipios_portal,
    count(*) FILTER (WHERE codigo_ibge IS NULL) AS sem_correspondencia,
    count(codigo_ibge) - count(DISTINCT codigo_ibge) AS ibge_repetidos
FROM silver.siafi_ibge;

-- Diagnóstico 3: peso dos grupos sem correspondência
SELECT count(*) AS grupos, coalesce(sum(valor_total), 0) AS valor_total
FROM silver.portal_bolsa_familia
WHERE codigo_ibge IS NULL;

-- Diagnóstico 4: os primeiros municípios sem correspondência
SELECT uf, municipio_portal
FROM silver.siafi_ibge
WHERE codigo_ibge IS NULL
ORDER BY uf, municipio_portal
LIMIT 30;