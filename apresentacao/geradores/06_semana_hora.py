"""Gera o widget 06_semana_hora.html: itens por dia da semana (mediana × média) e participação por hora, App × Site.

Dados:
- diario_qt.csv: qt_material total por dia (consulta no BigQuery);
- hora_canal.csv: participação de cada hora no total do próprio dia, média entre os dias, por canal
  (mesma lógica da seção 1.6 do notebook de análise exploratória).
"""
import sys
from pathlib import Path

import pandas as pd

diario = pd.read_csv(sys.argv[1], parse_dates=["dia"])
hora = pd.read_csv(sys.argv[2], index_col="hora")
destino = Path(sys.argv[3])
dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
mil = lambda v: f"{v / 1e3:.1f}".replace(".", ",")

s = diario.groupby(diario["dia"].dt.dayofweek)["qt"].agg(["mean", "median"])
geral = diario["qt"].median()

# ---- dia da semana: barras = mediana, traço = média
L, T, W, H = 34, 26, 400, 190
vmax = 55000
bw = W / 7
py = lambda v: T + H - v / vmax * H
p = [f'<line x1="{L}" x2="{L + W}" y1="{py(geral):.1f}" y2="{py(geral):.1f}" class="ref"/>']
for i, (dow, r) in enumerate(s.iterrows()):
    x = L + i * bw + 8
    forte = r["median"] >= geral * 1.08
    fraco = r["median"] <= geral * 0.9
    classe = "forte" if forte else "fraco" if fraco else "neutro"
    p.append(f'<rect x="{x:.1f}" y="{py(r["median"]):.1f}" width="{bw - 16:.1f}" height="{T + H - py(r["median"]):.1f}" rx="3" class="b {classe}"/>'
             f'<text x="{x + (bw - 16) / 2:.1f}" y="{py(r["median"]) - 6:.1f}" text-anchor="middle" class="v {classe}">{mil(r["median"])}</text>'
             f'<line x1="{x - 3:.1f}" x2="{x + bw - 13:.1f}" y1="{py(r["mean"]):.1f}" y2="{py(r["mean"]):.1f}" class="media{" sexta" if dow == 4 else ""}"/>'
             f'<text x="{x + (bw - 16) / 2:.1f}" y="{T + H + 16}" text-anchor="middle" class="eixo">{dias[dow]}</text>')
sexta = s.loc[4, "mean"]
xs = L + 4 * bw + (bw - 16) / 2 + 8
p.append(f'<text x="{xs:.1f}" y="{py(sexta) - 7:.1f}" text-anchor="middle" class="media-t">média {mil(sexta)} mil</text>'
         f'<text x="{xs:.1f}" y="{py(sexta) - 20:.1f}" text-anchor="middle" class="media-t2">Black Friday</text>')
svg_dia = f'<svg width="{L + W + 6}" height="{T + H + 24}">{"".join(p)}</svg>'

# ---- hora: participação no dia, App × Site
L2, T2, W2, H2 = 34, 14, 470, 190
hmax = 0.08
hx = lambda h: L2 + h / 23 * W2
hy = lambda v: T2 + H2 - v / hmax * H2
q = [f'<rect x="{hx(10):.1f}" y="{T2}" width="{hx(16) - hx(10):.1f}" height="{H2}" class="z-site"/>',
     f'<text x="{(hx(10) + hx(16)) / 2:.1f}" y="{T2 + 12}" text-anchor="middle" class="z-t site-t">Site: horário comercial</text>',
     f'<rect x="{hx(20):.1f}" y="{T2}" width="{hx(23) - hx(20):.1f}" height="{H2}" class="z-app"/>',
     f'<text x="{(hx(20) + hx(23)) / 2:.1f}" y="{T2 + 12}" text-anchor="middle" class="z-t app-t">App: noite</text>',
     f'<rect x="{hx(5.5):.1f}" y="{T2}" width="{hx(7.5) - hx(5.5):.1f}" height="{H2}" class="z-app"/>',
     f'<text x="{hx(6.5):.1f}" y="{T2 + 12}" text-anchor="middle" class="z-t app-t">App</text>']
for v in (0, 0.02, 0.04, 0.06, 0.08):
    q.append(f'<line x1="{L2}" x2="{L2 + W2}" y1="{hy(v):.1f}" y2="{hy(v):.1f}" class="grade"/>'
             f'<text x="{L2 - 6}" y="{hy(v) + 4:.1f}" text-anchor="end" class="eixo">{v:.0%}</text>')
for h in range(0, 24, 3):
    q.append(f'<text x="{hx(h):.1f}" y="{T2 + H2 + 16}" text-anchor="middle" class="eixo">{h}h</text>')
for canal, classe in (("Site", "site"), ("App", "app")):
    pts = " ".join(f"{hx(h):.1f},{hy(v):.1f}" for h, v in hora[canal].items())
    q.append(f'<polyline points="{pts}" class="l {classe}"/>')
q.append(f'<text x="{hx(23) + 6:.1f}" y="{hy(hora["App"][23]) - 2:.1f}" class="leg app-t">App</text>'
         f'<text x="{hx(23) + 6:.1f}" y="{hy(hora["Site"][23]) + 12:.1f}" class="leg site-t">Site</text>')
svg_hora = f'<svg width="{L2 + W2 + 36}" height="{T2 + H2 + 24}">{"".join(q)}</svg>'

valores = {
    "SVG_DIA": svg_dia, "SVG_HORA": svg_hora,
    "QUA": mil(s.loc[2, "median"]), "QUA_PCT": f"{s.loc[2, 'median'] / geral - 1:+.0%}",
    "DOM": mil(s.loc[6, "median"]), "DOM_PCT": f"{s.loc[6, 'median'] / geral - 1:+.0%}".replace("-", "−"),
    "SEX_MEDIA": mil(sexta), "GERAL": mil(geral), "SEX_MEDIANA": mil(s.loc[4, "median"]),
}
html = Path(__file__).with_name("06_semana_hora_modelo.html").read_text(encoding="utf-8")
for chave, valor in valores.items():
    html = html.replace("{{" + chave + "}}", valor)
destino.write_text(html, encoding="utf-8")
print("ok", destino, {k: v for k, v in valores.items() if not k.startswith("SVG")})
