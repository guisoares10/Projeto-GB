"""Gera o widget 05_app_site.html: preço de tabela × preço pago por item, App e Site, mês a mês.

Dados em canal_mensal.csv (consulta no BigQuery por mês × canal): ped, qt, rec (receita líquida) e des (desconto).
Preço pago por item = receita / itens (preço de tabela = (receita + desconto) / itens, só na tabela lateral).
"""
import sys
from pathlib import Path

import pandas as pd

m = pd.read_csv(sys.argv[1])
destino = Path(sys.argv[2])
nomes = {"2025-11": "nov", "2025-12": "dez", "2026-01": "jan", "2026-02": "fev",
         "2026-03": "mar", "2026-04": "abr", "2026-05": "mai", "2026-06": "jun"}
m["pago"] = m["rec"] / m["qt"]
m["tabela"] = (m["rec"] + m["des"]) / m["qt"]
m["sh_ped"] = m["ped"] / m.groupby("mes")["ped"].transform("sum")
w = m.pivot(index="mes", columns="canal")
meses = list(w.index)
tot = m.groupby("canal")[["ped", "qt", "rec", "des"]].sum()
pago = tot["rec"] / tot["qt"]
tabela = (tot["rec"] + tot["des"]) / tot["qt"]
tx = tot["des"] / (tot["rec"] + tot["des"])
sh_app = tot.loc["App", "ped"] / tot["ped"].sum()

L, T, W, H = 44, 10, 600, 262
y0, y1 = 20, 80
px = lambda i: L + 30 + i * (W - 60) / (len(meses) - 1)
py = lambda v: T + (y1 - v) / (y1 - y0) * H
partes = []
for v in range(20, 81, 20):
    partes.append(f'<line x1="{L}" x2="{L + W}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grade"/>'
                  f'<text x="{L - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="eixo">R$ {v}</text>')
for i, mes in enumerate(meses):
    partes.append(f'<text x="{px(i):.1f}" y="{T + H + 16}" text-anchor="middle" class="eixo">{nomes[mes]}</text>')


def linha(serie, classe):
    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(serie))
    return f'<polyline points="{pts}" class="{classe}"/>'


# faixa entre o preço pago no Site e no App
topo = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(w["pago"]["Site"]))
base = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in reversed(list(enumerate(w["pago"]["App"]))))
partes.append(f'<polygon points="{topo} {base}" class="gap"/>')
partes += [linha(w["pago"]["Site"], "pago site"), linha(w["pago"]["App"], "pago app")]
for i, mes in enumerate(meses):
    a, s = w["pago"]["App"][mes], w["pago"]["Site"][mes]
    partes.append(f'<circle cx="{px(i):.1f}" cy="{py(s):.1f}" r="3.5" class="pt site"/>'
                  f'<circle cx="{px(i):.1f}" cy="{py(a):.1f}" r="3.5" class="pt app"/>'
                  f'<text x="{px(i):.1f}" y="{py(a) + 17:.1f}" text-anchor="middle" class="dif">'
                  f'{100 * (a / s - 1):.0f}%</text>'.replace("-", "−"))
ult = len(meses) - 1
partes.append(f'<text x="{px(ult) + 10:.1f}" y="{py(w["pago"]["Site"][meses[-1]]) + 4:.1f}" class="leg site-l">Site</text>'
              f'<text x="{px(ult) + 10:.1f}" y="{py(w["pago"]["App"][meses[-1]]) + 4:.1f}" class="leg app-l">App</text>')
yb = T + H + 30
partes.append(f'<rect x="{L}" y="{yb}" width="{W}" height="24" rx="5" class="faixa"/>'
              f'<text x="{L - 6}" y="{yb + 16}" text-anchor="end" class="eixo">App</text>')
for i, mes in enumerate(meses):
    partes.append(f'<text x="{px(i):.1f}" y="{yb + 16}" text-anchor="middle" class="sh">{w["sh_ped"]["App"][mes]:.0%}</text>')
partes.append(f'<text x="{L}" y="{yb + 40}" class="eixo">participação do App nos pedidos de cada mês</text>')
svg = f'<svg width="{L + W + 50}" height="{yb + 46}" viewBox="0 0 {L + W + 50} {yb + 46}">{"".join(partes)}</svg>'


br = lambda v: f"R$ {v:.0f}"
valores = {
    "GRAFICO": svg, "SH_SITE": f"{1 - sh_app:.0%}",
    "DESC_PCT": f"{1 - pago['App'] / pago['Site']:.0%}",
    "TAB_APP": br(tabela["App"]), "TAB_SITE": br(tabela["Site"]),
    "TX_APP": f"{tx['App']:.0%}", "TX_SITE": f"{tx['Site']:.0%}",
    "PAGO_APP": br(pago["App"]), "PAGO_SITE": br(pago["Site"]),
    "SH_APP": f"{sh_app:.0%}",
}
html = Path(__file__).with_name("05_app_site_modelo.html").read_text(encoding="utf-8")
for chave, valor in valores.items():
    html = html.replace("{{" + chave + "}}", valor)
destino.write_text(html, encoding="utf-8")
print("ok", destino, {k: v for k, v in valores.items() if k != "GRAFICO"})
