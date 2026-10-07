"""Gera o widget 03_desconto.html: desconto × pedidos × receita e App × Site.

Números conferidos no BigQuery (fact_vendas, médias diárias por faixa de desconto do dia).
"""
import sys
from pathlib import Path

destino = Path(sys.argv[1])

# faixa: (rótulo, desconto médio, pedidos ×, receita ×, preço por item)
faixas = [
    ("até 30%", "26%", 1.00, 1.00, "R$ 74"),
    ("30–40%", "34%", 1.42, 1.16, "R$ 57"),
    ("40–50%", "44%", 1.68, 1.34, "R$ 53"),
    ("acima de 50%", "55%", 4.86, 2.87, "R$ 35"),
]
W, H = 560, 330
ML, MR, MT, MB = 34, 8, 30, 74
pw, ph = W - ML - MR, H - MT - MB
ymax = 5.5
y = lambda v: MT + ph - v / ymax * ph
grupo = pw / len(faixas)
larg = 34
partes = []
for v in [0, 1, 2, 3, 4, 5]:
    partes.append(f'<line x1="{ML}" x2="{W-MR}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grade"/>')
    partes.append(f'<text x="{ML-6}" y="{y(v)+4:.1f}" class="eixo" text-anchor="end">{v}×</text>')


def barra(x, valor, classe):
    topo = y(valor)
    base = MT + ph
    return (f'<path class="{classe}" d="M{x:.1f},{base} V{topo+4:.1f} Q{x:.1f},{topo:.1f} {x+4:.1f},{topo:.1f} '
            f'H{x+larg-4:.1f} Q{x+larg:.1f},{topo:.1f} {x+larg:.1f},{topo+4:.1f} V{base} Z"/>')


for i, (rot, tx, ped, rec, preco) in enumerate(faixas):
    cx = ML + grupo * i + grupo / 2
    x1, x2 = cx - larg - 1, cx + 1
    partes.append(barra(x1, ped, "b-ped"))
    partes.append(barra(x2, rec, "b-rec"))
    for x, v in [(x1, ped), (x2, rec)]:
        rotulo_valor = f"×{v:.1f}".replace(".", ",")
        partes.append(f'<text x="{x+larg/2:.1f}" y="{y(v)-5:.1f}" class="valor" text-anchor="middle">{rotulo_valor}</text>')
    partes.append(f'<text x="{cx:.1f}" y="{MT+ph+17}" class="cat" text-anchor="middle">{rot}</text>')
    partes.append(f'<text x="{cx:.1f}" y="{MT+ph+31}" class="sub" text-anchor="middle">média {tx}</text>')
    partes.append(f'<text x="{cx:.1f}" y="{MT+ph+50}" class="preco" text-anchor="middle">{preco}</text>')
partes.append(f'<line x1="{ML}" x2="{W-MR}" y1="{MT+ph}" y2="{MT+ph}" class="base"/>')
partes.append(f'<text x="{ML-30}" y="{MT+ph+50}" class="sub">preço/item</text>')
partes.append(f'<text x="{ML-30}" y="{MT+ph+17}" class="sub">desconto</text>')
partes.append(f'<text x="{ML-30}" y="{MT-14}" class="sub">crescimento por dia, em relação aos dias de desconto até 30%</text>')
svg = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">' + "".join(partes) + "</svg>"

modelo = Path(__file__).with_name("03_desconto_modelo.html").read_text(encoding="utf-8")
destino.write_text(modelo.replace("{{GRAFICO}}", svg), encoding="utf-8")
print("ok", destino)
