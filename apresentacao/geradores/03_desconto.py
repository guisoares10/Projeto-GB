"""Gera o widget 03_desconto.html: três estratégias de desconto × métrica, com variação contra o baseline.

Dados mensais em mensal_desconto.csv (consulta no BigQuery: pedidos, itens, receita e desconto por mês).
Base de comparação: média diária dos meses de dezembro a junho (sem a Black November).
"""
import sys
from pathlib import Path

import pandas as pd

mensal = pd.read_csv(sys.argv[1])
destino = Path(sys.argv[2])

mensal["preco"] = mensal["rec"] / mensal["qt"]
base = mensal[mensal["mes"] != "2025-11"]
ref = {
    "tx": base["des"].sum() / (base["rec"].sum() + base["des"].sum()),
    "ped_dia": base["ped"].sum() / base["dias"].sum(),
    "rec_dia": base["rec"].sum() / base["dias"].sum(),
    "preco": base["rec"].sum() / base["qt"].sum(),
}

br = lambda texto: texto.replace(".", ",")
linhas = [
    ("Desconto", "tx", lambda v: f"{v:.0%}", "pp", f"{ref['tx']:.0%}"),
    ("Pedidos/dia", "ped_dia", lambda v: f"{v / 1e3:.0f} mil", "pct", f"{ref['ped_dia'] / 1e3:.0f} mil"),
    ("Receita/dia", "rec_dia", lambda v: br(f"R$ {v / 1e6:.1f} mi"), "pct", br(f"R$ {ref['rec_dia'] / 1e6:.1f} mi")),
    ("Receita/item", "preco", lambda v: f"R$ {v:.0f}", "pct", f"R$ {ref['preco']:.0f}"),
]


def celula(valor, referencia, tipo):
    if tipo == "pp":
        delta = 100 * (valor - referencia)
        texto = f"{delta:+.0f} p.p."
        neutro = abs(delta) < 1.5
    else:
        delta = 100 * (valor / referencia - 1)
        texto = f"{delta:+.0f}%"
        neutro = abs(delta) < 2.5
    texto = texto.replace("-", "−")
    if neutro:
        return "neutro", "", texto.replace("+0 ", "0 ").replace("−0 ", "0 ").replace("+0%", "0%").replace("−0%", "0%")
    return ("sobe", "▲", texto) if delta > 0 else ("desce", "▼", texto)


grupos = [
    ("Black November", "nov", ["2025-11"], "nov",
     "Volume dispara, item rende menos"),
    ("Datas comemorativas", "dez (Natal) · mai (Mães)", ["2025-12", "2026-05"], "forte",
     "Desconto na média: a data puxa a venda"),
    ("Meses sem grande data", "jan · fev · mar · abr · jun", ["2026-01", "2026-02", "2026-03", "2026-04", "2026-06"], "",
     "Mesmo desconto, menos pedidos"),
]


def totais(df):
    return {
        "tx": df["des"].sum() / (df["rec"].sum() + df["des"].sum()),
        "ped_dia": df["ped"].sum() / df["dias"].sum(),
        "rec_dia": df["rec"].sum() / df["dias"].sum(),
        "preco": df["rec"].sum() / df["qt"].sum(),
    }


valores = [totais(mensal[mensal["mes"].isin(meses)]) for _, _, meses, _, _ in grupos]
cab = "".join(f'<th class="grupo {destaque}">{nome}<span>{meses_txt}</span></th>'
              for nome, meses_txt, _, destaque, _ in grupos)
corpo = []
for titulo, coluna, fmt, tipo, _ in linhas:
    tds = []
    for (_, _, _, destaque, _), v in zip(grupos, valores):
        classe, seta, texto = celula(v[coluna], ref[coluna], tipo)
        tds.append(f'<td class="{classe} {destaque}"><div class="delta"><span class="seta">{seta}</span>{texto}</div>'
                   f'<div class="abs">{fmt(v[coluna])}</div></td>')
    corpo.append(f'<tr><th class="linha">{titulo}</th>{"".join(tds)}</tr>')
leitura = "".join(f'<td class="motivo {destaque}">{texto}</td>' for _, _, _, destaque, texto in grupos)
corpo.append(f'<tr><th></th>{leitura}</tr>')
tabela = f'<table class="matriz"><tr><th class="linha"></th>{cab}</tr>{"".join(corpo)}</table>'
base_txt = " · ".join(f"{t.lower()} {r}" for t, _, _, _, r in linhas)

modelo = Path(__file__).with_name("03_desconto_modelo.html").read_text(encoding="utf-8")
destino.write_text(modelo.replace("{{MATRIZ}}", tabela).replace("{{BASE}}", base_txt), encoding="utf-8")
print("ok", destino, {k: round(v, 3) for k, v in ref.items()})
