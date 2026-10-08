"""Gera o widget 11_monitoramento.html: linha do tempo dos avisos do monitoramento de ingestão (dez–jun).

Dados em monitoramento_dia.csv: resultado da sql/45_sql_dq_monitoramento.sql rodada de 01/12/2025 a 30/06/2026
(novembro fora, inclusive do histórico), agregado por dia e check: n = horas (checks horários) ou categorias
(desconto) que dispararam no dia.
"""
import sys
from pathlib import Path

import pandas as pd

m = pd.read_csv(sys.argv[1], parse_dates=["dia"])
destino = Path(sys.argv[2])
dias = pd.date_range("2025-12-01", "2026-06-30")
faixas = [
    ("categoria_invalida", "Categoria inválida", "erro", "horas/dia"),
    ("receita_negativa", "Receita negativa", "erro", "horas/dia"),
    ("volume_outlier_iqr", "Volume diário", "outlier", "outlier IQR"),
    ("desconto_outlier_iqr", "Desconto por categoria", "desconto", "categorias/dia"),
]

L, T, W, FH, GAP = 172, 6, 540, 50, 10
x = lambda i: L + i * W / len(dias)
bw = W / len(dias)
p = []
for k, (check, nome, tipo, un) in enumerate(faixas):
    y0 = T + k * (FH + GAP)
    s = m[m["check_nome"] == check].set_index("dia")["n"].reindex(dias, fill_value=0)
    vmax = max(s.max(), 1)
    p.append(f'<rect x="{L}" y="{y0}" width="{W}" height="{FH}" rx="4" class="fundo"/>'
             f'<text x="{L - 10}" y="{y0 + FH / 2 - 2:.1f}" text-anchor="end" class="nome {tipo}">{nome}</text>'
             f'<text x="{L - 10}" y="{y0 + FH / 2 + 12:.1f}" text-anchor="end" class="un">{un}</text>')
    for i, v in enumerate(s):
        if v > 0:
            h = max(3, (FH - 6) * v / vmax)
            p.append(f'<rect x="{x(i):.2f}" y="{y0 + FH - 3 - h:.1f}" width="{max(bw - .6, 1):.2f}" height="{h:.1f}" class="b {tipo}"/>')
    dias_aviso = int((s > 0).sum())
    p.append(f'<text x="{L + W + 10}" y="{y0 + FH / 2 - 2:.1f}" class="tot {tipo}">{dias_aviso} dias</text>'
             f'<text x="{L + W + 10}" y="{y0 + FH / 2 + 12:.1f}" class="un">{int(s.sum())} avisos</text>')
yb = T + len(faixas) * (FH + GAP) - GAP
meses = {12: "dez", 1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun"}
for i, d in enumerate(dias):
    if d.day == 1:
        p.append(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{T}" y2="{yb + 4}" class="mes"/>'
                 f'<text x="{x(i) + 3:.1f}" y="{yb + 15}" class="eixo">{meses[d.month]}</text>')
svg = f'<svg width="{L + W + 70}" height="{yb + 20}">{"".join(p)}</svg>'

html = Path(__file__).with_name("11_monitoramento_modelo.html").read_text(encoding="utf-8")
destino.write_text(html.replace("{{SVG}}", svg), encoding="utf-8")
print("ok", destino)
