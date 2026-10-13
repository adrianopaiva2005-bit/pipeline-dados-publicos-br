import json
from datetime import date
from pathlib import Path

import requests

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
DESTINO = Path("data/bronze/ibge")


def baixar_municipios() -> list[dict]:
    resposta = requests.get(URL, timeout=60)
    resposta.raise_for_status()
    return resposta.json()


def salvar(dados: list[dict]) -> Path:
    DESTINO.mkdir(parents=True, exist_ok=True)
    caminho = DESTINO / f"municipios_{date.today():%Y%m%d}.json"
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return caminho


if __name__ == "__main__":
    dados = baixar_municipios()
    caminho = salvar(dados)
    print(f"{len(dados)} municípios salvos em {caminho}")