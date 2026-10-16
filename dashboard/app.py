"""Dashboard do Bolsa Família por município, lendo as tabelas gold."""

import os
from pathlib import Path

import plotly.express as px
import polars as pl
import psycopg
import streamlit as st
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

st.set_page_config(page_title="Bolsa Família por município", layout="wide")

SQL = """
SELECT
    competencia,
    codigo_ibge,
    municipio,
    uf,
    regiao,
    populacao,
    parcelas,
    valor_total::float8 AS valor_total,
    valor_total_per_capita::float8 AS valor_per_capita,
    parcelas_por_100_hab::float8 AS parcelas_por_100_hab
FROM gold.bolsa_familia_per_capita
"""


@st.cache_data(ttl=600)
def carregar() -> pl.DataFrame:
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        cur = conn.execute(SQL)
        colunas = [c.name for c in cur.description]
        linhas = cur.fetchall()
    return pl.DataFrame(
        linhas, schema=colunas, orient="row", infer_schema_length=None
    )


def brl(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


df = carregar()
competencia = df["competencia"].unique().to_list()
com_pop = df.filter(pl.col("populacao").is_not_null())

st.title("Bolsa Família por município")
st.caption(
    f"Competência {', '.join(competencia)}. Fontes: Portal da Transparência "
    "(pagamentos), IBGE (municípios) e SIDRA 4709 (população do Censo 2022)."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor total", brl(df["valor_total"].sum()))
c2.metric("Parcelas", inteiro(df["parcelas"].sum()))
c3.metric("Municípios", inteiro(df.height))
c4.metric("População (Censo 2022)", inteiro(com_pop["populacao"].sum()))

aba_regioes, aba_ranking, aba_municipios = st.tabs(
    ["Regiões", "Ranking", "Municípios"]
)

with aba_regioes:
    regioes = (
        com_pop.group_by("regiao")
        .agg(
            pl.col("valor_total").sum().alias("valor_total"),
            pl.col("populacao").sum().alias("populacao"),
            pl.col("parcelas").sum().alias("parcelas"),
        )
        .with_columns(
            (pl.col("valor_total") / pl.col("populacao")).alias("valor_per_capita")
        )
        .sort("valor_total", descending=True)
    )
    esq, dir_ = st.columns(2)
    with esq:
        fig = px.bar(
            regioes.with_columns((pl.col("valor_total") / 1e9).alias("valor_bi")),
            x="regiao",
            y="valor_bi",
            title="Valor total por região (R$ bilhões)",
            labels={"regiao": "Região", "valor_bi": "R$ bilhões"},
        )
        st.plotly_chart(fig, use_container_width=True, key="regiao_valor_total")
    with dir_:
        fig = px.bar(
            regioes.sort("valor_per_capita", descending=True),
            x="regiao",
            y="valor_per_capita",
            title="Valor per capita por região (R$ por habitante)",
            labels={"regiao": "Região", "valor_per_capita": "R$ por habitante"},
        )
        st.plotly_chart(fig, use_container_width=True, key="regiao_per_capita")
    st.caption(
        "O per capita regional exclui municípios sem população no Censo "
        "(hoje, só Boa Esperança do Norte, MT)."
    )

with aba_ranking:
    f1, f2, f3 = st.columns(3)
    metrica = f1.selectbox(
        "Ordenar por", ["Valor per capita", "Valor total", "Parcelas por 100 hab."]
    )
    n = f2.slider("Quantidade de municípios", 5, 50, 15)
    pop_min = f3.number_input("População mínima", min_value=0, value=0, step=1000)

    coluna = {
        "Valor per capita": "valor_per_capita",
        "Valor total": "valor_total",
        "Parcelas por 100 hab.": "parcelas_por_100_hab",
    }[metrica]

    base = com_pop.filter(pl.col("populacao") >= pop_min)
    top = (
        base.sort(coluna, descending=True)
        .head(n)
        .with_columns(
            (pl.col("municipio") + " (" + pl.col("uf") + ")").alias("rotulo")
        )
    )
    fig = px.bar(
        top,
        x=coluna,
        y="rotulo",
        orientation="h",
        title=f"Top {n} municípios por: {metrica}",
        labels={coluna: metrica, "rotulo": ""},
        hover_data=["populacao", "parcelas", "parcelas_por_100_hab"],
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True, key="ranking_municipios")

    if coluna != "valor_total":
        st.warning(
            "Os municípios com maiores valores per capita têm cerca de 37 a 39 "
            "parcelas por 100 habitantes, contra 9,26 no Brasil. Esse número ainda "
            "não foi confrontado com o número de famílias do painel do MDS, então "
            "deve ser lido com cautela. A população é de 2022 e os pagamentos, de 2026."
        )

with aba_municipios:
    b1, b2 = st.columns([2, 1])
    busca = b1.text_input("Buscar município")
    ufs = b2.multiselect("UF", sorted(df["uf"].unique().to_list()))

    tabela = df
    if busca:
        tabela = tabela.filter(
            pl.col("municipio").str.to_lowercase().str.contains(
                busca.lower(), literal=True
            )
        )
    if ufs:
        tabela = tabela.filter(pl.col("uf").is_in(ufs))

    tabela = tabela.select(
        "municipio",
        "uf",
        "regiao",
        "populacao",
        "parcelas",
        "valor_total",
        "valor_per_capita",
        "parcelas_por_100_hab",
    ).sort("valor_total", descending=True)

    rotulo_qtd = "município" if tabela.height == 1 else "municípios"
    st.caption(f"{inteiro(tabela.height)} {rotulo_qtd}")
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "municipio": "Município",
            "uf": "UF",
            "regiao": "Região",
            "populacao": st.column_config.NumberColumn("População", format="%d"),
            "parcelas": st.column_config.NumberColumn("Parcelas", format="%d"),
            "valor_total": st.column_config.NumberColumn("Valor total", format="R$ %.2f"),
            "valor_per_capita": st.column_config.NumberColumn(
                "Per capita", format="R$ %.2f"
            ),
            "parcelas_por_100_hab": st.column_config.NumberColumn(
                "Parcelas/100 hab.", format="%.2f"
            ),
        },
    )