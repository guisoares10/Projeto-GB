"""Gera o widget 04_categorias.html: papel de cada categoria (desconto, preço por item e participação na receita).

Dados mensais em categorias_mensal.csv (consulta no BigQuery por categoria × mês, sem a categoria inválida):
dias, qt (itens), rec (receita líquida) e des (desconto).
Protagonistas: perfumarias (receita), Gifts (valor por item) e Facial (desconto); as demais ficam em cinza.
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
PERFUMARIAS = {"PERFUMARIA MASCULINA", "PERFUMARIA FEMININA"}
m["tx"] = m["des"] / (m["rec"] + m["des"])
m["sh"] = m["rec"] / m.groupby("mes")["rec"].transform("sum")
tot = m.groupby("cat")[["qt", "rec", "des"]].sum()
tot["sh"] = tot["rec"] / tot["rec"].sum()
tot["pago"] = tot["rec"] / tot["qt"]
tot = tot.sort_values("rec", ascending=False)
media_pago = tot["rec"].sum() / tot["qt"].sum()
pct = lambda v: f"{100 * v:.0f}%"

# desconto: só a amplitude entre o menor e o maior mês (dez–jun)
DW, d0, d1 = 330, 0.15, 0.80
dx = lambda v: 34 + (v - d0) / (d1 - d0) * (DW - 68)
# preço pago por item
PW, pmax = 150, 110
# share: faixa mín–máx mensal e o total do período
SW, s1 = 170, 0.35
sx = lambda v: 4 + v / s1 * (SW - 8)

linhas = []
for c, t in tot.iterrows():
    mc = m[m["cat"] == c]
    fora = mc[mc["mes"] != "2025-11"]
    lo, hi = fora["tx"].min(), fora["tx"].max()
    facial, gift, perf = c == "FACIAL", c == "GIFTS", c in PERFUMARIAS
    papel = "facial" if facial else "gift" if gift else "perf" if perf else "outra"
    cor_d = {"facial": "#b5562b", "perf": "#d8aa90"}.get(papel, "#cfcfc7")
    cor_t = {"facial": "#b5562b", "perf": "#a9765a"}.get(papel, "#a3a39b")
    svg_d = (f'<svg width="{DW}" height="22">'
             f'<line x1="{dx(lo):.1f}" x2="{dx(hi):.1f}" y1="11" y2="11" stroke="{cor_d}" stroke-width="{6 if facial else 4}" stroke-linecap="round"/>'
             f'<text x="{dx(lo) - 7:.1f}" y="15" text-anchor="end" class="amp" fill="{cor_t}">{pct(lo)}</text>'
             f'<text x="{dx(hi) + 7:.1f}" y="15" class="amp" fill="{cor_t}">{pct(hi)}</text></svg>')

    svg_p = (f'<svg width="{PW}" height="18"><rect x="0" y="3" width="{t["pago"] / pmax * PW:.1f}" height="12" rx="2" '
             f'fill="{"#1d9e75" if gift else "#d3d6d4"}"/></svg>')

    slo, shi = mc["sh"].min(), mc["sh"].max()
    cor_s, cor_p = ("#1d9e75", "#137a5a") if gift else ("#cbd5d0", "#8c9690")
    svg_s = (f'<svg width="{SW}" height="22">'
             f'<line x1="{sx(slo):.1f}" x2="{sx(shi):.1f}" y1="11" y2="11" stroke="{cor_s}" stroke-width="6" stroke-linecap="round" stroke-opacity="{.6 if gift else 1}"/>'
             f'<circle cx="{sx(t["sh"]):.1f}" cy="11" r="4" fill="{cor_p}"/></svg>')

    linhas.append(
        f'<tr class="{papel}"><td class="nome">{nomes[c]}</td><td>{svg_d}</td>'
        f'<td class="sep"></td><td class="preco"><div class="barra">{svg_p}<b>R$&nbsp;{t["pago"]:.0f}</b></div></td>'
        f'<td class="sep"></td><td class="lado share">{pct(t["sh"])}</td><td class="lado">{svg_s}</td></tr>')

cab = ('<tr><th></th><th>Taxa de desconto: menor e maior mês<span>dez–jun</span></th><th class="sep"></th>'
       '<th class="preco esq">Preço pago por item</th><th class="sep"></th>'
       '<th class="lado" colspan="2">Share da receita<span>período · faixa entre o menor e o maior mês</span></th></tr>')
notas = ('<tr class="notas"><td colspan="2" class="nota d">{{NOTA_DESCONTO}}</td><td class="sep"></td>'
         '<td class="preco nota p">{{NOTA_PRECO}}</td><td class="sep"></td>'
         '<td colspan="2" class="lado nota s">{{NOTA_SHARE}}</td></tr>')
tabela = f'<table class="cats">{cab}{"".join(linhas)}{notas}</table>'

gifts = tot.loc["GIFTS"]
modelo = Path(__file__).with_name("04_categorias_modelo.html").read_text(encoding="utf-8")
for chave in ["NOTA_DESCONTO", "NOTA_PRECO", "NOTA_SHARE"]:
    ini, fim = f"<!--{chave}-->", f"<!--/{chave}-->"
    tabela = tabela.replace("{{" + chave + "}}", modelo[modelo.index(ini) + len(ini):modelo.index(fim)])
gm = m[m["cat"] == "GIFTS"]["sh"]
html = (modelo.replace("{{TABELA}}", tabela)
        .replace("{{MEDIA_PAGO}}", f"R$&nbsp;{media_pago:.0f}")
        .replace("{{GIFT_PAGO}}", f"R$&nbsp;{gifts['pago']:.0f}")
        .replace("{{GIFT_ITENS}}", pct(gifts["qt"] / tot["qt"].sum()))
        .replace("{{GIFT_REC}}", pct(gifts["sh"]))
        .replace("{{GIFT_MIN}}", pct(gm.min())).replace("{{GIFT_MAX}}", pct(gm.max()))
        .replace("{{PERF_SH}}", pct(tot.loc[list(PERFUMARIAS), "sh"].sum())))
destino.write_text(html, encoding="utf-8")
print("ok", destino)
