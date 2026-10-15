CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE FUNCTION silver.normaliza_nome(texto text)
RETURNS text AS $$
    SELECT trim(regexp_replace(upper(unaccent(texto)), '[^A-Z0-9]+', ' ', 'g'))
$$ LANGUAGE sql STABLE;

DROP TABLE IF EXISTS silver.portal_bolsa_familia;
DROP TABLE IF EXISTS silver.siafi_ibge;
DROP TABLE IF EXISTS silver.excecoes_siafi_ibge;

-- Municípios cuja grafia difere entre Portal e IBGE (pareados manualmente)
CREATE TABLE silver.excecoes_siafi_ibge (
    uf           text NOT NULL,
    codigo_siafi text NOT NULL,
    codigo_ibge  integer NOT NULL,
    PRIMARY KEY (uf, codigo_siafi)
);

INSERT INTO silver.excecoes_siafi_ibge (uf, codigo_siafi, codigo_ibge) VALUES
('BA', '3005', 2922250),
('BA', '3869', 2928505),
('CE', '1427', 2306306),
('MG', '4109', 3105509),
('MG', '4177', 3108909),
('MG', '4457', 3122900),
('MG', '5303', 3165206),
('MT', '9139', 5107008),
('MT', '9155', 5107800),
('PA', '0377', 1502954),
('PA', '0529', 1506500),
('PB', '0522', 2513968),
('PB', '2209', 2515401),
('PE', '2331', 2601607),
('PE', '3001', 2605459),
('PE', '2437', 2606903),
('PE', '2469', 2608503),
('RJ', '5875', 3303807),
('RJ', '5917', 3305901),
('RN', '1603', 2400208),
('RN', '1623', 2401206),
('RN', '1625', 2401305),
('RN', '1805', 2410306),
('RR', '0315', 1400605),
('RS', '8845', 4317103),
('SE', '3101', 2800100),
('SE', '3151', 2802601),
('SP', '6423', 3516101),
('SP', '7101', 3550001),
('TO', '9321', 1706001),
('TO', '0345', 1708254),
('TO', '9691', 1720499);

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
LEFT JOIN silver.excecoes_siafi_ibge e
    ON e.uf = p.uf
   AND e.codigo_siafi = p.codigo_siafi
LEFT JOIN silver.ibge_municipios i
    ON i.uf_sigla = p.uf
   AND (
        i.codigo_ibge = e.codigo_ibge
        OR (e.codigo_ibge IS NULL
            AND silver.normaliza_nome(i.nome) = silver.normaliza_nome(p.municipio))
   );

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

-- Diagnóstico 2: esperado 5571 municípios, 0 sem correspondência, 0 repetidos, 5571 distintos
SELECT
    count(*) AS municipios_portal,
    count(*) FILTER (WHERE codigo_ibge IS NULL) AS sem_correspondencia,
    count(codigo_ibge) - count(DISTINCT codigo_ibge) AS ibge_repetidos,
    count(DISTINCT codigo_ibge) AS ibge_distintos
FROM silver.siafi_ibge;

-- Diagnóstico 3: grupos sem correspondência (esperado 0)
SELECT count(*) AS grupos, coalesce(sum(valor_total), 0) AS valor_total
FROM silver.portal_bolsa_familia
WHERE codigo_ibge IS NULL;

-- Diagnóstico 4: municípios do IBGE que ficaram sem uso (esperado 0 linhas)
SELECT i.uf_sigla, i.codigo_ibge, i.nome
FROM silver.ibge_municipios i
WHERE NOT EXISTS (
    SELECT 1 FROM silver.siafi_ibge s WHERE s.codigo_ibge = i.codigo_ibge
)
ORDER BY i.uf_sigla, i.nome;