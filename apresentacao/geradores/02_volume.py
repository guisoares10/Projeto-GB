"""Gera o widget 02_volume.html (EDA: volume, itens por pedido, App × Site, novembro).

Dados semanais vêm de semanal.csv (consulta no BigQuery: qt_material e nr_pedidos por semana).
"""
import sys
from pathlib import Path

import pandas as pd

semanal = pd.read_csv(sys.argv[1], parse_dates=["semana"])
destino = Path(sys.argv[2])
semanal["media_dia"] = semanal["qt"] / semanal["dias"]

# área do gráfico
W, H = 650, 425
ML, MR, MT, MB = 46, 10, 34, 64
pw, ph = W - ML - MR, H - MT - MB
n = len(semanal)
passo = pw / n
larg = passo - 3
ymax = 200_000
y = lambda v: MT + ph - v / ymax * ph

black_nov = (semanal["semana"] >= "2025-11-03") & (semanal["semana"] <= "2025-11-24")
partes = []
# grade e eixo y
for v in range(0, ymax + 1, 50_000):
    partes.append(f'<line x1="{ML}" x2="{W-MR}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grade"/>')
    partes.append(f'<text x="{ML-8}" y="{y(v)+4:.1f}" class="eixo" text-anchor="end">{v//1000}</text>')
partes.append(f'<text x="{ML-36}" y="{MT-14}" class="eixo">mil itens/dia</text>')
# faixa da Black November
i0 = semanal.index[black_nov][0]; i1 = semanal.index[black_nov][-1]
x0 = ML + i0 * passo; x1 = ML + (i1 + 1) * passo
partes.append(f'<rect x="{x0:.1f}" y="{MT-6}" width="{x1-x0:.1f}" height="{ph+6}" class="faixa"/>')
partes.append(f'<text x="{(x0+x1)/2:.1f}" y="{MT+8}" class="faixa-rot" text-anchor="middle">Black November</text>')
# barras
for i, r in semanal.iterrows():
    x = ML + i * passo + 1.5
    topo = y(r["media_dia"])
    classe = "barra destaque" if black_nov[i] else "barra"
    altura = MT + ph - topo
    partes.append(
        f'<path class="{classe}" d="M{x:.1f},{MT+ph} V{topo+3:.1f} Q{x:.1f},{topo:.1f} {x+3:.1f},{topo:.1f} '
        f'H{x+larg-3:.1f} Q{x+larg:.1f},{topo:.1f} {x+larg:.1f},{topo+3:.1f} V{MT+ph} Z"/>'
    )
# eventos (semana que contém a data)
# (nome, data, altura do rótulo em itens/dia)
eventos = [("Black Friday", "2025-11-28", None), ("Natal", "2025-12-25", 80_000),
           ("Dia do Consumidor", "2026-03-15", 80_000), ("Dia das Mães", "2026-05-10", 80_000),
           ("Namorados", "2026-06-12", 80_000)]
for nome, data, altura in eventos:
    d = pd.Timestamp(data)
    i = semanal.index[(semanal["semana"] <= d) & (semanal["semana"] + pd.Timedelta(days=6) >= d)][0]
    cx = ML + i * passo + passo / 2
    topo = y(semanal.loc[i, "media_dia"])
    if altura is None:  # rótulo ao lado da barra
        partes.append(f'<text x="{cx+passo/2+4:.1f}" y="{topo+10:.1f}" class="evento">{nome}</text>')
        continue
    base_rot = y(altura)
    partes.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{base_rot+4:.1f}" y2="{topo-3:.1f}" class="guia"/>')
    partes.append(f'<circle cx="{cx:.1f}" cy="{base_rot+4:.1f}" r="2.5" class="ponto"/>')
    partes.append(f'<text x="{cx:.1f}" y="{base_rot-3:.1f}" class="evento" text-anchor="middle">{nome}</text>')
# eixo x: meses
meses = semanal.groupby(semanal["semana"].dt.to_period("M")).head(1)
nomes = {11: "nov", 12: "dez", 1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun"}
for i, r in meses.iterrows():
    if r["semana"].month == 10:  # semana parcial de 27/10 (só 01 e 02/11)
        continue
    x = ML + i * passo
    partes.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{MT+ph}" y2="{MT+ph+6}" class="tick"/>')
    partes.append(f'<text x="{x+4:.1f}" y="{MT+ph+18}" class="eixo">{nomes[r["semana"].month]}</text>')
partes.append(f'<line x1="{ML}" x2="{W-MR}" y1="{MT+ph}" y2="{MT+ph}" class="base"/>')
partes.append(f'<text x="{ML}" y="{H-24}" class="nota">Média diária de itens vendidos em cada semana (segunda a domingo).</text>')
partes.append(f'<text x="{ML}" y="{H-6}" class="nota-destaque">Antes das datas comemorativas a base forma picos: a compra se antecipa à data.</text>')
svg = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">' + "".join(partes) + "</svg>"

html = (Path(__file__).with_name("02_volume_modelo.html")).read_text(encoding="utf-8").replace("{{GRAFICO}}", svg)
destino.write_text(html, encoding="utf-8")
print("ok", destino)
