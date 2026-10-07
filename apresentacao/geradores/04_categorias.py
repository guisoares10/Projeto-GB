"""Gera o widget 04_categorias.html: desconto mês a mês, preço por item e participação na receita, por categoria.

Dados mensais em categorias_mensal.csv (consulta no BigQuery por categoria × mês, sem a categoria inválida):
dias, qt (itens), rec (receita líquida) e des (desconto).
"""
import sys
from pathlib import Path

import pandas as pd

m = pd.read_csv(sys.argv[1])
destino = Path(sys.argv[2])
nomes = {
    "PERFUMARIA MASCULINA": "Perfumaria Masculina", "PERFUMARIA FEMININA": "Perfumaria Feminina",
    "CORPO E BANHO": "Corpo e Banho", "PERF. DE ENTRADA E DEOS": "Perf. de Entrada e Deos",
    "GIFTS": "Gifts", "MAQUIAGEM": "Maquiagem", "CABELOS": "Cabelos", "FACIAL": "Facial",
}
m["tx"] = m["des"] / (m["rec"] + m["des"])
m["sh"] = m["rec"] / m.groupby("mes")["rec"].transform("sum")
tot = m.groupby("cat")[["qt", "rec", "des"]].sum()
tot["sh"] = tot["rec"] / tot["rec"].sum()
tot["pago"] = tot["rec"] / tot["qt"]
tot["tabela"] = (tot["rec"] + tot["des"]) / tot["qt"]
tot = tot.sort_values("rec", ascending=False)
media_pago = tot["rec"].sum() / tot["qt"].sum()
pct = lambda v: f"{100 * v:.0f}%"

# desconto: pontos dos meses dez–jun, novembro à parte; destaque para amplitude ≥ 20 p.p. fora de novembro
DW, d0, d1 = 210, 0.15, 0.80
dx = lambda v: 8 + (v - d0) / (d1 - d0) * (DW - 16)
# share: faixa mín–máx mensal e o total do período
SW, s1 = 150, 0.35
sx = lambda v: 4 + v / s1 * (SW - 8)
# preço pago por item
PW, pmax = 150, 110

linhas = []
for i, (c, t) in enumerate(tot.iterrows(), 1):
    mc = m[m["cat"] == c]
    fora = mc[mc["mes"] != "2025-11"]
    nov = mc.loc[mc["mes"] == "2025-11", "tx"].iloc[0]
    lo, hi = fora["tx"].min(), fora["tx"].max()
    oscila = hi - lo >= 0.20
    cor = "#b5562b" if oscila else "#9a9a90"
    pontos = "".join(f'<circle cx="{dx(v):.1f}" cy="13" r="3.6" fill="{cor}" fill-opacity=".75"/>' for v in fora["tx"])
    svg_d = (f'<svg width="{DW}" height="26"><line x1="8" x2="{DW - 8}" y1="13" y2="13" stroke="#eeeeea"/>'
             f'<line x1="{dx(lo):.1f}" x2="{dx(hi):.1f}" y1="13" y2="13" stroke="{cor}" stroke-width="{4 if oscila else 2}" stroke-opacity=".35"/>'
             f'{pontos}<rect x="{dx(nov) - 4:.1f}" y="9" width="8" height="8" transform="rotate(45 {dx(nov):.1f} 13)" fill="#1d9e75"/></svg>')
    faixa_d = f'<span class="faixa{" forte" if oscila else ""}">{pct(lo)}–{pct(hi)}</span>'

    gift = c == "GIFTS"
    svg_p = (f'<svg width="{PW}" height="18"><rect x="0" y="3" width="{t["pago"] / pmax * PW:.1f}" height="12" rx="2" '
             f'fill="{"#1d9e75" if gift else "#a3aba7"}"/></svg>')

    slo, shi = mc["sh"].min(), mc["sh"].max()
    larga = shi - slo >= 0.09
    svg_s = (f'<svg width="{SW}" height="22"><line x1="4" x2="{SW - 4}" y1="11" y2="11" stroke="#d7e9e1"/>'
             f'<line x1="{sx(slo):.1f}" x2="{sx(shi):.1f}" y1="11" y2="11" stroke="#1d9e75" stroke-width="6" stroke-linecap="round" stroke-opacity="{.55 if larga else .3}"/>'
             f'<circle cx="{sx(t["sh"]):.1f}" cy="11" r="4" fill="#137a5a"/></svg>')

    linhas.append(
        f'<tr class="{"gift" if gift else ""}"><td class="nome">{nomes[c]}</td>'
        f'<td>{svg_d}</td><td class="num">{faixa_d}</td>'
        f'<td class="sep"></td><td class="preco"><div class="barra">{svg_p}<b>R$ {t["pago"]:.0f}</b></div></td>'
        f'<td class="sep"></td><td class="lado rank">{i}</td><td class="lado share">{pct(t["sh"])}</td>'
        f'<td class="lado">{svg_s}</td><td class="lado num{" forte-s" if larga else ""}">{pct(slo)}–{pct(shi)}</td></tr>')

cab = ('<tr><th></th><th class="esq">Taxa de desconto por mês<span>● dez–jun &nbsp;<i class="losango"></i> nov</span></th>'
       '<th>dez–jun</th><th class="sep"></th><th class="preco esq">Preço pago por item</th><th class="sep"></th>'
       '<th class="lado" colspan="2">Top 8 receita</th><th class="lado esq">Share da receita por mês<span>faixa mín–máx · ● período</span></th>'
       '<th class="lado">mín–máx</th></tr>')
notas = ('<tr class="notas"><td colspan="3" class="nota d">{{NOTA_DESCONTO}}</td><td class="sep"></td>'
         '<td class="preco nota p">{{NOTA_PRECO}}</td><td class="sep"></td>'
         '<td colspan="4" class="lado nota s">{{NOTA_SHARE}}</td></tr>')
tabela = f'<table class="cats">{cab}{"".join(linhas)}{notas}</table>'

gifts = tot.loc["GIFTS"]
modelo = Path(__file__).with_name("04_categorias_modelo.html").read_text(encoding="utf-8")
for chave in ["NOTA_DESCONTO", "NOTA_PRECO", "NOTA_SHARE"]:
    ini, fim = f"<!--{chave}-->", f"<!--/{chave}-->"
    tabela = tabela.replace("{{" + chave + "}}", modelo[modelo.index(ini) + len(ini):modelo.index(fim)])
html = (modelo.replace("{{TABELA}}", tabela)
        .replace("{{MEDIA_PAGO}}", f"R$&nbsp;{media_pago:.0f}")
        .replace("{{GIFT_PAGO}}", f"R$&nbsp;{gifts['pago']:.0f}")
        .replace("{{GIFT_TABELA}}", f"R$&nbsp;{gifts['tabela']:.0f}")
        .replace("{{GIFT_ITENS}}", pct(gifts["qt"] / tot["qt"].sum()))
        .replace("{{GIFT_REC}}", pct(gifts["sh"])))
destino.write_text(html, encoding="utf-8")
print("ok", destino)
print(tot.round(3))
