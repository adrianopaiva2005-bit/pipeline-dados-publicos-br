"""Orquestra o pipeline de ponta a ponta, parando no primeiro erro."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
SQL_DIR = RAIZ / "sql"

# Cada etapa: (tipo, nome, é_ingestão)
ETAPAS = [
    ("py", "ingest_ibge", True),
    ("py", "load_ibge", False),
    ("sql", "silver_ibge_municipios.sql", False),
    ("py", "ingest_portal", True),
    ("py", "load_portal", False),
    ("sql", "silver_portal_bolsa_familia.sql", False),
    ("sql", "gold_bolsa_familia_municipio.sql", False),
    ("py", "ingest_populacao", True),
    ("py", "load_populacao", False),
    ("sql", "gold_bolsa_familia_per_capita.sql", False),
]


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def rodar_python(modulo: str) -> None:
    env = {**os.environ, "PYTHONPATH": str(RAIZ / "src")}
    subprocess.run(
        [sys.executable, "-m", f"pipeline.{modulo}"],
        cwd=RAIZ,
        env=env,
        check=True,
    )


def rodar_sql(arquivo: str) -> None:
    texto = (SQL_DIR / arquivo).read_text(encoding="utf-8")
    # Sem parâmetros, o psycopg aceita vários comandos no mesmo arquivo.
    with conectar() as conn:
        conn.execute(texto)
        conn.commit()


def rodar_testes() -> None:
    subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=RAIZ, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pular-ingestao",
        action="store_true",
        help="não baixa dados novamente; usa o que já está em data/",
    )
    parser.add_argument(
        "--sem-testes",
        action="store_true",
        help="não roda o pytest no final",
    )
    args = parser.parse_args()

    load_dotenv(RAIZ / ".env")
    inicio = time.perf_counter()

    for tipo, nome, eh_ingestao in ETAPAS:
        if eh_ingestao and args.pular_ingestao:
            print(f"[pulada] {nome}")
            continue

        print(f"[inicio] {nome}")
        t0 = time.perf_counter()
        try:
            if tipo == "py":
                rodar_python(nome)
            else:
                rodar_sql(nome)
        except Exception as erro:
            print(f"[ERRO] {nome}: {erro}")
            return 1
        print(f"[ok] {nome} ({time.perf_counter() - t0:.1f}s)")

    if not args.sem_testes:
        print("[inicio] pytest")
        try:
            rodar_testes()
        except subprocess.CalledProcessError:
            print("[ERRO] testes falharam")
            return 1

    print(f"Pipeline concluído em {time.perf_counter() - inicio:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())