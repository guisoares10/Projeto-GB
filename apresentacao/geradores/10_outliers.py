"""Gera o widget 10_outliers.html: outliers diários (IQR) de dezembro a junho, sem novembro.

Dados em diario_sem_nov.csv (consulta no BigQuery: itens, pedidos, receita e desconto por dia, sem novembro).
Limites de Tukey calculados só com dez–jun: Q1 − 1,5 × IQR e Q3 + 1,5 × IQR.
"""
import sys
from pathlib import Path

import pandas as pd

d = pd.read_csv(sys.argv[1], parse_dates=["dia"]).sort_values("dia").reset_index(drop=True)
destino = Path(sys.argv[2])


def limites(s):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


flags = {}
for col in ["qt", "ped", "rec", "tx"]:
    li, ls = limites(d[col])
    flags[col] = (d[col] < li) | (d[col] > ls)
_, ls_qt = limites(d["qt"])
q1_qt, q3_qt = d["qt"].quantile(0.25), d["qt"].quantile(0.75)
algum = flags["qt"] | flags["ped"] | flags["rec"]

# grupos de leitura dos dias extremos
datas = {"2025-12-01": "data", "2026-05-05": "data", "2026-05-07": "data", "2026-05-08": "data", "2026-05-09": "data"}
d["tipo"] = d["dia"].dt.strftime("%Y-%m-%d").map(datas).fillna("desconto")

L, T, W, H = 46, 16, 600, 290
vmax = 80000
px = lambda i: L + i / (len(d) - 1) * W
py = lambda v: T + H - v / vmax * H
p = [f'<rect x="{L}" y="{py(q3_qt):.1f}" width="{W}" height="{py(q1_qt) - py(q3_qt):.1f}" class="faixa"/>',
     f'<line x1="{L}" x2="{L + W}" y1="{py(ls_qt):.1f}" y2="{py(ls_qt):.1f}" class="lim"/>',
     f'<text x="{L + 140}" y="{py(ls_qt) + 15:.1f}" class="lim-t">limite superior (Q3 + 1,5 × IQR) · {ls_qt / 1e3:.0f} mil</text>']
for v in range(0, 80001, 20000):
    p.append(f'<line x1="{L}" x2="{L + W}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grade"/>'
             f'<text x="{L - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="eixo">{v // 1000} mil</text>')
meses = {12: "dez", 1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun"}
for m, g in d.groupby(d["dia"].dt.month, sort=False):
    i = g.index[0]
    p.append(f'<line x1="{px(i):.1f}" x2="{px(i):.1f}" y1="{T + H}" y2="{T + H + 4}" class="tick"/>'
             f'<text x="{px(i) + 3:.1f}" y="{T + H + 16}" class="eixo">{meses[m]}</text>')
pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in d["qt"].items())
p.append(f'<polyline points="{pts}" class="serie"/>')
for i, r in d[flags["qt"]].iterrows():
    p.append(f'<circle cx="{px(i):.1f}" cy="{py(r["qt"]):.1f}" r="4.5" class="pt {r["tipo"]}"/>')
rot = [("2025-12-01", "Pré-Natal", "start", 6), ("2025-12-12", "12/12", "start", 6),
       ("2026-05-08", "Dia das Mães", "end", -8), ("2026-05-21", "20–21/05", "start", 8), ("2026-06-30", "30/06", "end", -8)]
for dia, txt, anc, dx in rot:
    i = d.index[d["dia"] == pd.Timestamp(dia)][0]
    p.append(f'<text x="{px(i) + dx:.1f}" y="{py(d.loc[i, "qt"]) - 7:.1f}" text-anchor="{anc}" class="rot">{txt}</text>')
svg = f'<svg width="{L + W + 8}" height="{T + H + 22}">{"".join(p)}</svg>'

n = len(d)
pct = lambda k: f"{k / n:.1%}".replace(".", ",")
valores = {
    "SVG": svg, "N": str(n),
    "QT": str(int(flags["qt"].sum())), "QT_P": pct(flags["qt"].sum()),
    "PED": str(int(flags["ped"].sum())), "PED_P": pct(flags["ped"].sum()),
    "REC": str(int(flags["rec"].sum())), "REC_P": pct(flags["rec"].sum()),
    "UNIAO": str(int(algum.sum())), "TX_MED": f"{d['tx'].median():.0%}",
}
html = Path(__file__).with_name("10_outliers_modelo.html").read_text(encoding="utf-8")
for k, v in valores.items():
    html = html.replace("{{" + k + "}}", v)
destino.write_text(html, encoding="utf-8")
print("ok", {k: v for k, v in valores.items() if k != "SVG"})
