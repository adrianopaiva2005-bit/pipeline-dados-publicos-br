import csv
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

CAMINHO_PADRAO = Path("data/bronze/portal_transparencia/202608_NovoBolsaFamilia.csv")
COLUNAS = [
    "MÊS COMPETÊNCIA",
    "MÊS REFERÊNCIA",
    "UF",
    "CÓDIGO MUNICÍPIO SIAFI",
    "NOME MUNICÍPIO",
    "VALOR PARCELA",
]


def agregar(caminho: Path):
    grupos = defaultdict(lambda: [0, Decimal("0")])
    lidas = 0
    descartadas = 0

    with open(caminho, encoding="latin-1", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        cabecalho = next(leitor)
        faltando = [c for c in COLUNAS if c not in cabecalho]
        if faltando:
            raise SystemExit(f"Colunas não encontradas no cabeçalho: {faltando}")
        i_comp, i_ref, i_uf, i_siafi, i_nome, i_valor = (
            cabecalho.index(c) for c in COLUNAS
        )

        for linha in leitor:
            lidas += 1
            try:
                valor = Decimal(linha[i_valor].replace(".", "").replace(",", "."))
                chave = (
                    linha[i_comp],
                    linha[i_ref],
                    linha[i_uf],
                    linha[i_siafi],
                    linha[i_nome],
                )
            except (IndexError, InvalidOperation):
                descartadas += 1
                continue
            grupo = grupos[chave]
            grupo[0] += 1
            grupo[1] += valor
            if lidas % 5_000_000 == 0:
                print(f"{lidas:,} linhas lidas...")

    return grupos, lidas, descartadas


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else CAMINHO_PADRAO
    if not caminho.exists():
        raise SystemExit(
            f"CSV do Portal não encontrado: {caminho}\n"
            "Baixe o arquivo do Portal da Transparência (Novo Bolsa Família, "
            "competência 202608) e coloque-o nessa pasta antes de executar."
        )
    grupos, lidas, descartadas = agregar(caminho)

    saida = caminho.with_name(caminho.stem + "_agregado.csv")
    with open(saida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(
            ["competencia", "referencia", "uf", "codigo_siafi", "municipio",
             "parcelas", "valor_total"]
        )
        for chave in sorted(grupos):
            parcelas, total = grupos[chave]
            escritor.writerow([*chave, parcelas, f"{total:.2f}"])

    print(f"linhas lidas: {lidas:,}")
    print(f"linhas descartadas: {descartadas:,}")
    print(f"grupos gerados: {len(grupos):,}")
    print(f"arquivo: {saida}")


if __name__ == "__main__":
    main()