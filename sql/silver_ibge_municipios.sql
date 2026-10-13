CREATE SCHEMA IF NOT EXISTS silver;

DROP TABLE IF EXISTS silver.ibge_municipios;

CREATE TABLE silver.ibge_municipios AS
SELECT
    id AS codigo_ibge,
    payload ->> 'nome' AS nome,
    COALESCE(
        payload #>> '{microrregiao,mesorregiao,UF,sigla}',
        payload #>> '{regiao-imediata,regiao-intermediaria,UF,sigla}'
    ) AS uf_sigla,
    COALESCE(
        payload #>> '{microrregiao,mesorregiao,UF,nome}',
        payload #>> '{regiao-imediata,regiao-intermediaria,UF,nome}'
    ) AS uf_nome,
    COALESCE(
        payload #>> '{microrregiao,mesorregiao,UF,regiao,nome}',
        payload #>> '{regiao-imediata,regiao-intermediaria,UF,regiao,nome}'
    ) AS regiao_nome,
    carregado_em
FROM bronze.ibge_municipios;

ALTER TABLE silver.ibge_municipios ADD PRIMARY KEY (codigo_ibge);