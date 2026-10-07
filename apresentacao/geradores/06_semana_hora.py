"""Gera o widget 06_semana_hora.html: itens por dia da semana (mediana) e mapa de calor dia da semana × hora.

Dados:
- diario_qt.csv: qt_material total por dia (consulta no BigQuery);
- semana_hora.csv: participação de cada hora no total do próprio dia, média entre os dias de cada dia da semana.
"""
import sys
from pathlib import Path

import pandas as pd

diario = pd.read_csv(sys.argv[1], parse_dates=["dia"])
grade = pd.read_csv(sys.argv[2], index_col="dow")
grade.columns = grade.columns.astype(int)
destino = Path(sys.argv[3])
dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
mil = lambda v: f"{v / 1e3:.1f}".replace(".", ",")

s = diario.groupby(diario["dia"].dt.dayofweek)["qt"].agg(["mean", "median"])
geral = diario["qt"].median()

# ---- dia da semana: barras = mediana
L, T, W, H = 8, 22, 400, 200
vmax = 36000
bw = W / 7
py = lambda v: T + H - v / vmax * H
p = [f'<line x1="{L}" x2="{L + W}" y1="{py(geral):.1f}" y2="{py(geral):.1f}" class="ref"/>']
for i, (dow, r) in enumerate(s.iterrows()):
    x = L + i * bw + 8
    classe = "forte" if r["median"] >= geral * 1.08 else "fraco" if r["median"] <= geral * 0.9 else "neutro"
    p.append(f'<rect x="{x:.1f}" y="{py(r["median"]):.1f}" width="{bw - 16:.1f}" height="{T + H - py(r["median"]):.1f}" rx="3" class="b {classe}"/>'
             f'<text x="{x + (bw - 16) / 2:.1f}" y="{py(r["median"]) - 6:.1f}" text-anchor="middle" class="v {classe}">{mil(r["median"])}</text>'
             f'<text x="{x + (bw - 16) / 2:.1f}" y="{T + H + 16}" text-anchor="middle" class="eixo">{dias[dow]}</text>')
svg_dia = f'<svg width="{L + W + 6}" height="{T + H + 24}">{"".join(p)}</svg>'

# ---- mapa de calor dia da semana × hora
L2, T2, cw, ch = 34, 16, 20, 25
vtop = 0.075
def cor(v):
    t = min(max((v - 0.02) / (vtop - 0.02), 0), 1) ** 1.3
    a, b = (247, 247, 244), (19, 122, 90)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))
q = []
for h in range(0, 24, 3):
    q.append(f'<text x="{L2 + h * cw + cw / 2:.1f}" y="{T2 - 4}" text-anchor="middle" class="eixo">{h}h</text>')
for i, dow in enumerate(grade.index):
    y = T2 + i * ch
    q.append(f'<text x="{L2 - 6}" y="{y + ch / 2 + 4:.1f}" text-anchor="end" class="eixo{" forte-t" if dow in (5, 6) else ""}">{dias[dow]}</text>')
    for h in range(24):
        q.append(f'<rect x="{L2 + h * cw + 1:.1f}" y="{y + 1:.1f}" width="{cw - 2}" height="{ch - 2}" rx="2" fill="{cor(grade.loc[dow, h])}"/>')
# destaques: sábado de manhã e domingo à noite
def caixa(dow, h0, h1, rotulo, lado):
    i = list(grade.index).index(dow)
    x0, x1, y = L2 + h0 * cw, L2 + (h1 + 1) * cw, T2 + i * ch
    return (f'<rect x="{x0:.1f}" y="{y:.1f}" width="{x1 - x0:.1f}" height="{ch}" rx="3" class="destaque"/>'
            f'<text x="{(x0 + x1) / 2:.1f}" y="{T2 + 7 * ch + 15:.1f}" text-anchor="middle" class="dest-t">{rotulo}</text>')
q.append(caixa(5, 9, 12, f"sáb 11h: {grade.loc[5, 11]:.1%}".replace(".", ","), "dir"))
q.append(caixa(6, 20, 22, f"dom 21h: {grade.loc[6, 21]:.1%}".replace(".", ","), "esq"))
HW = L2 + 24 * cw
svg_hora = f'<svg width="{HW + 8}" height="{T2 + 7 * ch + 22}">{"".join(q)}</svg>'

leg = "".join(f'<i style="background:{cor(v)}"></i>' for v in (0.02, 0.031, 0.042, 0.053, 0.064, 0.075))

valores = {
    "SVG_DIA": svg_dia, "SVG_HORA": svg_hora, "LEG": leg, "GERAL": mil(geral),
    "QUA_PCT": f"{s.loc[2, 'median'] / geral - 1:+.0%}",
    "DOM_PCT": f"{s.loc[6, 'median'] / geral - 1:+.0%}".replace("-", "−"),
    "SEX_MEDIA": mil(s.loc[4, "mean"]), "SEX_MEDIANA": mil(s.loc[4, "median"]),
    "SAB_NOITE": f"{grade.loc[5, 21]:.1%}".replace(".", ","), "DOM_NOITE": f"{grade.loc[6, 21]:.1%}".replace(".", ","),
    "COMERCIAL": f"{grade.loc[:, 10:17].sum(axis=1).mean():.0%}", "NOITE": f"{grade.loc[:, 18:23].sum(axis=1).mean():.0%}",
    "MADRUGADA": f"{grade.loc[:, 0:5].sum(axis=1).mean():.0%}",
}
html = Path(__file__).with_name("06_semana_hora_modelo.html").read_text(encoding="utf-8")
for chave, valor in valores.items():
    html = html.replace("{{" + chave + "}}", valor)
destino.write_text(html, encoding="utf-8")
print("ok", destino, {k: v for k, v in valores.items() if not k.startswith(("SVG", "LEG"))})
