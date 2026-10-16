import json
from datetime import date
from pathlib import Path

import requests

URL = "https://apisidra.ibge.gov.br/values/t/4709/n6/all/v/93/p/2022"
DESTINO = Path("data/bronze/ibge")


def main() -> None:
    resposta = requests.get(URL, timeout=180)
    resposta.raise_for_status()
    dados = resposta.json()

    cabecalho, linhas = dados[0], dados[1:]
    print("Cabeçalho da resposta:")
    for campo, descricao in cabecalho.items():
        print(f"  {campo}: {descricao}")

    campo_codigo = next(
        (c for c, d in cabecalho.items() if d.startswith("Município") and "Código" in d),
        None,
    )
    if campo_codigo is None:
        raise SystemExit("Não achei a coluna do código do município no cabeçalho.")

    codigos = set()
    total = 0
    sem_valor = 0
    for linha in linhas:
        codigos.add(linha[campo_codigo])
        try:
            total += int(linha["V"])
        except ValueError:
            sem_valor += 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    arquivo = DESTINO / f"populacao_2022_{date.today():%Y%m%d}.json"
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    print(f"Campo do código do município: {campo_codigo}")
    print(f"Linhas de dados: {len(linhas)}")
    print(f"Municípios distintos: {len(codigos)}")
    print(f"Linhas sem valor numérico: {sem_valor}")
    print(f"População total: {total}")
    print(f"Arquivo salvo em: {arquivo}")


if __name__ == "__main__":
    main()