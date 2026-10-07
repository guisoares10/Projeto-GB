"""Gera o widget 04_categorias.html: resposta de itens e receita ao desconto, por categoria.

Dados em categorias_desconto.csv (consulta diária no BigQuery por categoria, sem categoria inválida):
- qt_10pp / rec_10pp: variação de itens / receita do dia associada a +10 p.p. de desconto
  (regressão de log(itens) e log(receita) na taxa de desconto do dia, com dia da semana, fora de novembro);
- sh_rec / sh_des: participação na receita e no desconto do período.
"""
import sys
from pathlib import Path

import pandas as pd

cat = pd.read_csv(sys.argv[1]).set_index("cat")
destino = Path(sys.argv[2])
nomes = {
    "CABELOS": ("Cabelos", 8, -12, "start"),
    "CORPO E BANHO": ("Corpo e Banho", -22, 4, "end"),
    "FACIAL": ("Facial", 0, 26, "middle"),
    "GIFTS": ("Gifts", 0, 24, "middle"),
    "MAQUIAGEM": ("Maquiagem", 0, 25, "middle"),
    "PERF. DE ENTRADA E DEOS": ("Entrada e Deos", 20, 8, "start"),
    "PERFUMARIA FEMININA": ("Perf. Feminina", -26, 4, "end"),
    "PERFUMARIA MASCULINA": ("Perf. Masculina", -30, -6, "end"),
}

L, T, W, H = 46, 12, 460, 246
x0, x1, y0, y1 = 0, 70, -10, 40
px = lambda v: L + (v - x0) / (x1 - x0) * W
py = lambda v: T + (y1 - v) / (y1 - y0) * H
br = lambda v: f"{v:+.0f}%".replace("-", "−")

partes = [f'<rect x="{L}" y="{py(5):.1f}" width="{W}" height="{py(y0) - py(5):.1f}" fill="#fbeee6"/>',
          f'<text x="{L + W - 6}" y="{py(y0) - 8:.1f}" text-anchor="end" class="zona">desconto quase não vira receita</text>']
for v in range(0, 41, 10):
    partes.append(f'<line x1="{L}" x2="{L + W}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grade"/>'
                  f'<text x="{L - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="eixo">{br(v)}</text>')
for v in range(0, 71, 10):
    partes.append(f'<text x="{px(v):.1f}" y="{T + H + 16}" text-anchor="middle" class="eixo">{br(v)}</text>')
partes.append(f'<line x1="{L}" x2="{L + W}" y1="{py(0):.1f}" y2="{py(0):.1f}" class="zero"/>')
for c, r in cat.sort_values("sh_rec", ascending=False).iterrows():
    x, y = px(100 * r["qt_10pp"]), py(100 * r["rec_10pp"])
    raio = 4 + 30 * r["sh_rec"] ** 0.5
    fraca = r["rec_10pp"] < 0.05
    cor = "#c9764a" if fraca else "#1d9e75"
    nome, dx, dy, ancora = nomes[c]
    partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor}" fill-opacity=".22" stroke="{cor}" stroke-width="1.5"/>'
                  f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{ancora}" class="nome">{nome}'
                  f'<tspan class="sub"> {r["sh_rec"]:.0%}</tspan></text>'.replace("%</tspan>", "% rec.</tspan>"))
partes.append(f'<text x="{L + W / 2}" y="{T + H + 34}" text-anchor="middle" class="tit-eixo">itens vendidos com +10 p.p. de desconto</text>'
              f'<text transform="translate(12 {T + H / 2}) rotate(-90)" text-anchor="middle" class="tit-eixo">receita com +10 p.p. de desconto</text>')
svg = f'<svg width="{L + W + 20}" height="{T + H + 40}" viewBox="0 0 {L + W + 20} {T + H + 40}">{"".join(partes)}</svg>'

modelo = Path(__file__).with_name("04_categorias_modelo.html").read_text(encoding="utf-8")
destino.write_text(modelo.replace("{{GRAFICO}}", svg), encoding="utf-8")
print("ok", destino)
