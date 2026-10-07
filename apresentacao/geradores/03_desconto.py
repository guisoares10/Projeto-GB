"""Gera o widget 03_desconto.html: matriz mês × métrica com variação contra a média de dez–jun.

Dados mensais em mensal_desconto.csv (consulta no BigQuery: pedidos, itens, receita e desconto por mês).
Base de comparação: média diária dos meses de dezembro a junho (sem a Black November).
"""
import sys
from pathlib import Path

import pandas as pd

mensal = pd.read_csv(sys.argv[1])
destino = Path(sys.argv[2])
nomes = {"2025-11": "nov", "2025-12": "dez", "2026-01": "jan", "2026-02": "fev",
         "2026-03": "mar", "2026-04": "abr", "2026-05": "mai", "2026-06": "jun"}

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
        return "neutro", "", texto.replace("+0", "0")
    return ("sobe", "▲", texto) if delta > 0 else ("desce", "▼", texto)


cab = "".join(f'<th class="{"nov" if m == "2025-11" else ""}">{nomes[m]}</th>' for m in mensal["mes"])
corpo = []
for titulo, coluna, fmt, tipo, ref_txt in linhas:
    tds = []
    for _, r in mensal.iterrows():
        classe, seta, texto = celula(r[coluna], ref[coluna], tipo)
        extra = " nov" if r["mes"] == "2025-11" else ""
        tds.append(f'<td class="{classe}{extra}"><div class="delta"><span class="seta">{seta}</span>{texto}</div>'
                   f'<div class="abs">{fmt(r[coluna])}</div></td>')
    corpo.append(f'<tr><th class="linha">{titulo}</th>{"".join(tds)}</tr>')
motivos = {
    "2025-11": "Black November",
    "2025-12": "Natal: compras de 1 a 21/12",
    "2026-01": "pós-festas: desconto não reverte",
    "2026-02": "Carnaval e desconto baixo após 08/02",
    "2026-03": "Dia da Mulher e Consumidor",
    "2026-04": "sem datas e menos desconto",
    "2026-05": "Dia das Mães e campanha 15–24/05",
    "2026-06": "Namorados sem pico; promo 27–30/06",
}
linha_motivo = "".join(f'<td class="motivo{" nov" if m == "2025-11" else ""}">{motivos[m]}</td>' for m in mensal["mes"])
corpo.append(f'<tr><th class="linha motivo-tit">O que explica</th>{linha_motivo}</tr>')
tabela = f'<table class="matriz"><tr><th class="linha"></th>{cab}</tr>{"".join(corpo)}</table>'

modelo = Path(__file__).with_name("03_desconto_modelo.html").read_text(encoding="utf-8")
receita_base = br(f"R$ {ref['rec_dia'] / 1e6:.1f} mi")
base_txt = (f"<b>Base*</b> — desconto {ref['tx']:.0%} · pedidos {ref['ped_dia'] / 1e3:.0f} mil/dia · "
            f"receita {receita_base}/dia · receita/item R$ {ref['preco']:.0f}")
destino.write_text(modelo.replace("{{MATRIZ}}", tabela).replace("{{BASE}}", base_txt), encoding="utf-8")
print("ok", destino, {k: round(v, 3) for k, v in ref.items()})
