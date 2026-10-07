"""Gera o widget 03_desconto.html: desconto, pedidos e receita por mês (novembro em destaque) e App × Site.

Dados mensais em mensal_desconto.csv (consulta no BigQuery: pedidos, receita e desconto por mês).
"""
import sys
from pathlib import Path

import pandas as pd

mensal = pd.read_csv(sys.argv[1])
destino = Path(sys.argv[2])
nomes = {"2025-11": "nov", "2025-12": "dez", "2026-01": "jan", "2026-02": "fev",
         "2026-03": "mar", "2026-04": "abr", "2026-05": "mai", "2026-06": "jun"}

nov = mensal[mensal["mes"] == "2025-11"].iloc[0]
demais = mensal[mensal["mes"] != "2025-11"]
tx_demais = demais["des"].sum() / (demais["rec"].sum() + demais["des"].sum())
ped_demais = demais["ped"].sum() / demais["dias"].sum()
rec_demais = demais["rec"].sum() / demais["dias"].sum()

linhas = [
    ("Taxa de desconto", "tx", lambda v: f"{v:.0%}", f"+{100 * (nov['tx'] - tx_demais):.0f} p.p.", 0.62),
    ("Pedidos por dia", "ped_dia", lambda v: f"{v / 1e3:.0f} mil", f"+{100 * (nov['ped_dia'] / ped_demais - 1):.0f}%", 82_000),
    ("Receita por dia", "rec_dia", lambda v: f"R$ {v / 1e6:.1f} mi".replace(".", ","), f"+{100 * (nov['rec_dia'] / rec_demais - 1):.0f}%", 4.8e6),
]

W, H_LINHA, TOPO_ROT = 580, 104, 16
ML = 118
n = len(mensal)
passo = (W - ML - 6) / n
larg = passo * 0.62
partes = []
for k, (titulo, coluna, fmt, variacao, ymax) in enumerate(linhas):
    y0 = k * H_LINHA
    base = y0 + H_LINHA - 18
    altura_max = H_LINHA - 18 - TOPO_ROT - 4
    partes.append(f'<text x="0" y="{y0 + 38}" class="titulo-linha">{titulo}</text>')
    partes.append(f'<text x="0" y="{y0 + 62}" class="seta">▲ {variacao}</text>')
    partes.append(f'<text x="0" y="{y0 + 77}" class="seta-sub">em novembro</text>')
    partes.append(f'<line x1="{ML}" x2="{W}" y1="{base}" y2="{base}" class="base"/>')
    for i, r in mensal.iterrows():
        x = ML + i * passo + (passo - larg) / 2
        h = r[coluna] / ymax * altura_max
        topo = base - h
        classe = "b-nov" if r["mes"] == "2025-11" else "b-mes"
        partes.append(
            f'<path class="{classe}" d="M{x:.1f},{base} V{topo + 3:.1f} Q{x:.1f},{topo:.1f} {x + 3:.1f},{topo:.1f} '
            f'H{x + larg - 3:.1f} Q{x + larg:.1f},{topo:.1f} {x + larg:.1f},{topo + 3:.1f} V{base} Z"/>'
        )
        partes.append(f'<text x="{x + larg / 2:.1f}" y="{topo - 4:.1f}" class="{"v-nov" if classe == "b-nov" else "v-mes"}" '
                      f'text-anchor="middle">{fmt(r[coluna])}</text>')
    if k == len(linhas) - 1:
        for i, r in mensal.iterrows():
            partes.append(f'<text x="{ML + i * passo + passo / 2:.1f}" y="{base + 14}" class="mes" text-anchor="middle">{nomes[r["mes"]]}</text>')
H = len(linhas) * H_LINHA
svg = f'<svg viewBox="0 -4 {W} {H + 4}" width="{W}" height="{H + 4}">' + "".join(partes) + "</svg>"

modelo = Path(__file__).with_name("03_desconto_modelo.html").read_text(encoding="utf-8")
destino.write_text(modelo.replace("{{GRAFICO}}", svg), encoding="utf-8")
print("ok", destino, {"tx_demais": round(tx_demais, 3), "ped_demais": round(ped_demais), "rec_demais": round(rec_demais)})
