"""Gera o widget 15_resultado_modelos.html: real × modelo vencedor × média móvel de 7 dias no teste (01/04 a 30/06).

Dados em teste_diario.csv: total do dia real e previsto no teste faseado do modelo por categoria
(LightGBM com parâmetros padrão e baseline mm7), gerado com o pacote gb_ml.
"""
import sys
from pathlib import Path

import pandas as pd

t = pd.read_csv(sys.argv[1], parse_dates=["data"]).reset_index(drop=True)
destino = Path(sys.argv[2])

L, T, W, H = 44, 10, 600, 200
vmax = 80000
px = lambda i: L + i / (len(t) - 1) * W
py = lambda v: T + H - v / vmax * H
p = []
for v in range(0, 80001, 20000):
    p.append(f'<line x1="{L}" x2="{L + W}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grade"/>'
             f'<text x="{L - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="eixo">{v // 1000} mil</text>')
for i, d in t["data"].items():
    if d.day == 1:
        p.append(f'<line x1="{px(i):.1f}" x2="{px(i):.1f}" y1="{T}" y2="{T + H}" class="mes"/>'
                 f'<text x="{px(i) + 4:.1f}" y="{T + H + 15}" class="eixo">{["", "", "", "", "abril", "maio", "junho"][d.month]}</text>')
for col, classe in (("mm7", "mm7"), ("real", "real"), ("lightgbm", "lgb")):
    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in t[col].items())
    p.append(f'<polyline points="{pts}" class="l {classe}"/>')
svg = f'<svg width="{L + W + 8}" height="{T + H + 22}">{"".join(p)}</svg>'
html = Path(__file__).with_name("15_resultado_modelos_modelo.html").read_text(encoding="utf-8")
destino.write_text(html.replace("{{SVG}}", svg), encoding="utf-8")
print("ok", destino)
