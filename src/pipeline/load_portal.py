import argparse
import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(override=True)

COMPETENCIA_PADRAO = "202608"

DDL = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.portal_bolsa_familia (
    competencia  text NOT NULL,
    referencia   text NOT NULL,
    uf           text NOT NULL,
    codigo_siafi text NOT NULL,
    municipio    text NOT NULL,
    parcelas     integer NOT NULL,
    valor_total  numeric(18, 2) NOT NULL
);
"""


def caminho_agregado(competencia: str) -> Path:
    return Path(
        "data/bronze/portal_transparencia/"
        f"{competencia}_NovoBolsaFamilia_agregado.csv"
    )


def main(competencia: str = COMPETENCIA_PADRAO):
    caminho = caminho_agregado(competencia)
    if not caminho.exists():
        raise SystemExit(
            f"Agregado do Portal não encontrado: {caminho}\n"
            f"Execute a ingestão da competência {competencia} antes da carga."
        )

    with open(caminho, encoding="utf-8", newline="") as f:
        competencias = sorted({linha["competencia"] for linha in csv.DictReader(f)})
    if competencias != [competencia]:
        raise SystemExit(
            f"O arquivo {caminho} contém as competências {competencias}, "
            f"mas a carga pediu apenas {competencia}."
        )

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute(
                "DELETE FROM bronze.portal_bolsa_familia WHERE competencia = %s",
                (competencia,),
            )
            with open(caminho, encoding="utf-8") as f:
                with cur.copy(
                    "COPY bronze.portal_bolsa_familia "
                    "FROM STDIN WITH (FORMAT csv, HEADER true)"
                ) as copy:
                    while bloco := f.read(1024 * 1024):
                        copy.write(bloco)

            cur.execute(
                "SELECT count(*), sum(parcelas), sum(valor_total), "
                "count(*) FILTER (WHERE codigo_siafi LIKE '0%%') "
                "FROM bronze.portal_bolsa_familia WHERE competencia = %s",
                (competencia,),
            )
            linhas, parcelas, valor, com_zero = cur.fetchone()

    print(f"competência carregada: {competencia}")
    print(f"linhas da competência: {linhas:,}")
    print(f"soma de parcelas: {parcelas:,}")
    print(f"soma de valor_total: {valor:,.2f}")
    print(f"códigos SIAFI com zero à esquerda: {com_zero:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--competencia", default=COMPETENCIA_PADRAO, help="AAAAMM")
    main(parser.parse_args().competencia)
