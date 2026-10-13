import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

ORIGEM = Path("data/bronze/ibge")


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def carregar() -> int:
    caminho = sorted(ORIGEM.glob("municipios_*.json"))[-1]
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    with conectar() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bronze.ibge_municipios (
                id integer,
                payload jsonb,
                arquivo_origem text,
                carregado_em timestamptz DEFAULT now()
            )
            """
        )
        conn.execute("TRUNCATE bronze.ibge_municipios")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO bronze.ibge_municipios (id, payload, arquivo_origem) "
                "VALUES (%s, %s::jsonb, %s)",
                [(m["id"], json.dumps(m), caminho.name) for m in dados],
            )
    return len(dados)


if __name__ == "__main__":
    print(f"{carregar()} municípios carregados em bronze.ibge_municipios")