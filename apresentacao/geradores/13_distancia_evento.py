"""Gera o widget 13_distancia_evento.html: como funcionam dias_ate_evento e dias_desde_evento.

Exemplo real: itens por dia em torno do Dia das Mães 2026 (diario_sem_nov.csv) e o valor das features
calculado pelo pacote (gb_ml.features.features_calendario).
"""
import sys
from pathlib import Path

import pandas as pd

from gb_ml.features import features_calendario

d = pd.read_csv(sys.argv[1], parse_dates=["dia"])
destino = Path(sys.argv[2])
janela = d[d["dia"].between("2026-04-26", "2026-05-24")].reset_index(drop=True)
f = features_calendario(janela["dia"])
janela = pd.concat([janela, f[["dias_ate_evento", "dias_desde_evento", "evento_dia_maes"]]], axis=1)

L, T, W, H = 40, 22, 600, 160
n = len(janela)
bw = W / n
vmax = 72000
py = lambda v: T + H - v / vmax * H
p = []
for v in (0, 20000, 40000, 60000):
    p.append(f'<line x1="{L}" x2="{L + W}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grade"/>'
             f'<text x="{L - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="eixo">{v // 1000} mil</text>')
for i, r in janela.iterrows():
    x = L + i * bw
    classe = "dia" if r["dias_ate_evento"] == 0 else ("antes" if r["dias_ate_evento"] < 15 else "depois")
    p.append(f'<rect x="{x + 1.5:.1f}" y="{py(r["qt"]):.1f}" width="{bw - 3:.1f}" height="{T + H - py(r["qt"]):.1f}" rx="2" class="b {classe}"/>')
# faixas de valores das features
y1, y2, y3 = T + H + 18, T + H + 40, T + H + 62
p.append(f'<text x="{L - 6}" y="{y1 + 4}" text-anchor="end" class="lbl">até</text>'
         f'<text x="{L - 6}" y="{y2 + 4}" text-anchor="end" class="lbl">desde</text>'
         f'<text x="{L - 6}" y="{y3 + 4}" text-anchor="end" class="lbl">flag</text>')
for i, r in janela.iterrows():
    cx = L + i * bw + bw / 2
    a, s, fl = int(r["dias_ate_evento"]), int(r["dias_desde_evento"]), int(r["evento_dia_maes"])
    p.append(f'<text x="{cx:.1f}" y="{y1 + 4}" text-anchor="middle" class="v{" on" if a < 15 else ""}">{a}</text>'
             f'<text x="{cx:.1f}" y="{y2 + 4}" text-anchor="middle" class="v{" on" if s < 15 else ""}">{s}</text>'
             f'<text x="{cx:.1f}" y="{y3 + 4}" text-anchor="middle" class="v{" flag" if fl else ""}">{fl}</text>')
    if r["dia"].day in (1, 10, 20) or i == 0:
        p.append(f'<text x="{cx:.1f}" y="{y3 + 24}" text-anchor="middle" class="eixo">{r["dia"]:%d/%m}</text>')
i10 = janela.index[janela["dia"] == pd.Timestamp("2026-05-10")][0]
cx = L + i10 * bw + bw / 2
p.append(f'<text x="{cx:.1f}" y="{py(janela.loc[i10, "qt"]) - 6:.1f}" text-anchor="middle" class="ev">10/05</text>')
i20 = janela.index[janela["dia"] == pd.Timestamp("2026-05-20")][0]
p.append(f'<text x="{L + (i20 + 1) * bw:.1f}" y="{T - 6}" text-anchor="middle" class="camp">campanha de maio</text>')
svg = f'<svg width="{L + W + 6}" height="{y3 + 30}">{"".join(p)}</svg>'

html = Path(__file__).with_name("13_distancia_evento_modelo.html").read_text(encoding="utf-8")
destino.write_text(html.replace("{{SVG}}", svg), encoding="utf-8")
print("ok", destino)
