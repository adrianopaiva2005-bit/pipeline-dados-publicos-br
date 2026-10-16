import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

ARQUIVOS = sorted(Path("data/bronze/ibge").glob("populacao_2022_*.json"))

DDL = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.ibge_populacao (
    codigo_ibge  integer PRIMARY KEY,
    municipio    text NOT NULL,
    ano          integer NOT NULL,
    populacao    integer NOT NULL,
    carregado_em timestamptz NOT NULL DEFAULT now()
);
"""


def main() -> None:
    if not ARQUIVOS:
        raise SystemExit("Nenhum arquivo populacao_2022_*.json encontrado.")
    arquivo = ARQUIVOS[-1]
    dados = json.loads(arquivo.read_text(encoding="utf-8"))[1:]

    registros = [
        (int(l["D1C"]), l["D1N"], int(l["D3C"]), int(l["V"]))
        for l in dados
    ]

    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute("TRUNCATE bronze.ibge_populacao")
            cur.executemany(
                "INSERT INTO bronze.ibge_populacao "
                "(codigo_ibge, municipio, ano, populacao) VALUES (%s, %s, %s, %s)",
                registros,
            )
            cur.execute("SELECT count(*), sum(populacao) FROM bronze.ibge_populacao")
            linhas, total = cur.fetchone()

    print(f"Arquivo: {arquivo}")
    print(f"Linhas carregadas: {linhas}")
    print(f"População total: {total}")


if __name__ == "__main__":
    main()