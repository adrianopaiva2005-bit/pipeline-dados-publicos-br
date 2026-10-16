import os
from decimal import Decimal

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv()

VALOR_TOTAL = Decimal("12763249759.00")
PARCELAS_TOTAL = 18809420
POPULACAO_TOTAL = 203080756
VALOR_REFERENCIA_ATUAL = Decimal("12742332559.00")


@pytest.fixture(scope="module")
def cur():
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as c:
            yield c


def test_gold_municipio_uma_linha_por_municipio(cur):
    cur.execute(
        "SELECT count(*), count(DISTINCT codigo_ibge) FROM gold.bolsa_familia_municipio"
    )
    linhas, distintos = cur.fetchone()
    assert linhas == 5571
    assert distintos == 5571


def test_gold_municipio_totais_conferem(cur):
    cur.execute("SELECT sum(valor_total), sum(parcelas) FROM gold.bolsa_familia_municipio")
    valor, parcelas = cur.fetchone()
    assert valor == VALOR_TOTAL
    assert parcelas == PARCELAS_TOTAL


def test_per_capita_preserva_totais(cur):
    cur.execute(
        "SELECT count(*), sum(valor_total), sum(populacao) FROM gold.bolsa_familia_per_capita"
    )
    linhas, valor, populacao = cur.fetchone()
    assert linhas == 5571
    assert valor == VALOR_TOTAL
    assert populacao == POPULACAO_TOTAL


def test_per_capita_so_boa_esperanca_do_norte_sem_populacao(cur):
    cur.execute("SELECT codigo_ibge FROM gold.bolsa_familia_per_capita WHERE populacao IS NULL")
    assert cur.fetchall() == [(5101837,)]


def test_cobertura_nao_passa_de_40_parcelas_por_100_hab(cur):
    cur.execute("SELECT max(parcelas_por_100_hab) FROM gold.bolsa_familia_per_capita")
    assert cur.fetchone()[0] < 40


def test_valor_referencia_atual_confere_com_silver(cur):
    cur.execute("SELECT sum(valor_referencia_atual) FROM gold.bolsa_familia_per_capita")
    valor_gold = cur.fetchone()[0]
    cur.execute(
        "SELECT sum(valor_total) FROM silver.portal_bolsa_familia WHERE referencia = competencia"
    )
    valor_silver = cur.fetchone()[0]
    assert valor_gold == valor_silver
    assert valor_gold == VALOR_REFERENCIA_ATUAL
    