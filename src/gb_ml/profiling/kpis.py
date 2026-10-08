"""KPIs da análise exploratória: base mês × canal × categoria e as visões padrão.

As seções de KPI do notebook seguem o mesmo roteiro (geral, linha do tempo, canal,
categoria, canal × categoria). KPIs de soma mostram valor absoluto e share; KPIs de
razão são recalculados a partir das somas em cada recorte (média ponderada).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display
from matplotlib.ticker import FuncFormatter

# KPIs de razão: numerador e denominador são somados antes de dividir (média ponderada)
RAZOES = {
    "itens_por_pedido": lambda d: d["qt_material"] / d["nr_pedidos"],
    "preco_medio_item": lambda d: d["receita_aprovada"] / d["qt_material"],
    "taxa_desconto": lambda d: d["vlr_venda_desconto"] / (d["receita_aprovada"] + d["vlr_venda_desconto"]),
}
ROTULOS = {
    "qt_material": "qt_material",
    "nr_pedidos": "nr_pedidos",
    "itens_por_pedido": "itens por pedido = qt_material / nr_pedidos",
    "receita_aprovada": "receita_aprovada (R$)",
    "preco_medio_item": "preço médio por item = receita_aprovada / qt_material (R$)",
    "taxa_desconto": "taxa de desconto (%)",
}
CANAIS = ["App", "Site"]
CORES_CANAL = {"App": "#1f4e79", "Site": "#d17a22"}
PALETA = ["#1f4e79", "#2e86ab", "#8c564b", "#6a994e", "#c9a227", "#d17a22", "#a23b72", "#7d5ba6"]
INVALIDA = "CATEGORIA_INVALIDA"
SOMAS = ["qt_material", "nr_pedidos", "receita_aprovada", "vlr_venda_desconto"]


def preparar_base(base: pd.DataFrame) -> pd.DataFrame:
    """Padroniza a base vinda do BigQuery: mês como texto AAAA-MM e métricas em float."""
    base = base.copy()
    base["mes"] = pd.to_datetime(base["mes"]).dt.strftime("%Y-%m")
    base[SOMAS] = base[SOMAS].astype(float)
    return base


def agregar(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Soma as métricas base no nível `por` e recalcula os KPIs de razão."""
    out = df.groupby(por, as_index=False)[SOMAS].sum() if por else df[SOMAS].sum().to_frame().T
    for nome, formula in RAZOES.items():
        out[nome] = formula(out)
    return out


def formatar(valor: float, metrica: str) -> str:
    """Formato curto para rótulos: mil/mi, R$ e %."""
    if metrica == "taxa_desconto":
        return f"{valor:.1%}"
    if metrica == "itens_por_pedido":
        return f"{valor:.2f}"
    prefixo = "R$ " if metrica in ("receita_aprovada", "preco_medio_item") else ""
    if metrica == "preco_medio_item":
        return f"{prefixo}{valor:,.2f}"
    if abs(valor) >= 1e6:
        return f"{prefixo}{valor / 1e6:,.1f} mi"
    if abs(valor) >= 1e3:
        return f"{prefixo}{valor / 1e3:,.0f} mil"
    return f"{prefixo}{valor:,.0f}"


def eh_soma(metrica: str) -> bool:
    return metrica not in RAZOES


def eixo(ax, metrica: str, eixo_valor: str = "y") -> None:
    """Formata o eixo de valores no mesmo padrão dos rótulos (mil/mi, R$, %)."""
    alvo = ax.yaxis if eixo_valor == "y" else ax.xaxis
    alvo.set_major_formatter(FuncFormatter(lambda v, _: formatar(v, metrica) if v != 0 else "0"))


class PainelKPI:
    """Visões padrão dos KPIs sobre a base mês × canal × categoria.

    Categorias ordenadas por volume (maior primeiro), com a inválida por último, em cinza.
    """

    def __init__(self, base: pd.DataFrame):
        self.base = base
        self.categorias = (
            base[base["des_categoria_material"] != INVALIDA]
            .groupby("des_categoria_material")["qt_material"].sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
        self.cores = dict(zip(self.categorias, PALETA))
        self.categorias_com_invalida = self.categorias + [INVALIDA]
        self.cores_com_invalida = {**self.cores, INVALIDA: "#b0b0b0"}

    def geral(self, metricas: list[str]) -> None:
        """Tabela com o valor total do período de cada KPI."""
        total = agregar(self.base, [])
        display(pd.DataFrame({
            "kpi": metricas,
            "total_periodo": [formatar(total[m].iloc[0], m) for m in metricas],
        }))


    def linha_do_tempo(self, metricas: list[str]) -> None:
        """Evolução mensal de cada KPI (barras para soma, linha para razão)."""
        mensal = agregar(self.base, ["mes"]).sort_values("mes")
        fig, axes = plt.subplots(1, len(metricas), figsize=(8 * len(metricas), 4.5), squeeze=False)
        for ax, m in zip(axes[0], metricas):
            if eh_soma(m):
                barras = ax.bar(mensal["mes"], mensal[m], color="#1f4e79")
                ax.bar_label(barras, labels=[formatar(v, m) for v in mensal[m]], fontsize=7, padding=2)
            else:
                ax.plot(mensal["mes"], mensal[m], marker="o", color="#1f4e79")
                for x, v in zip(mensal["mes"], mensal[m]):
                    ax.annotate(formatar(v, m), (x, v), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=7)
                ax.margins(y=0.2)
            ax.set_title(f"{ROTULOS[m]} por mês")
            eixo(ax, m)
            ax.tick_params(axis="x", rotation=45)
            ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        plt.show()


    def por_canal(self, metricas: list[str]) -> None:
        """Por canal: à esquerda o total do período; à direita a evolução mensal.

        Soma: barras com valor e share; mês a mês empilhado com o share de cada canal no rótulo.
        Razão: valor por canal e linhas mês a mês.
        """
        geral = agregar(self.base, ["des_canal_venda_final_agrup"]).set_index("des_canal_venda_final_agrup").loc[CANAIS]
        mensal = agregar(self.base, ["mes", "des_canal_venda_final_agrup"])
        fig, axes = plt.subplots(len(metricas), 2, figsize=(16, 4.5 * len(metricas)), squeeze=False,
                                 gridspec_kw={"width_ratios": [1, 2.2]})
        for linha, m in zip(axes, metricas):
            ax = linha[0]
            barras = ax.bar(CANAIS, geral[m], color=[CORES_CANAL[c] for c in CANAIS])
            if eh_soma(m):
                share = geral[m] / geral[m].sum()
                rotulos = [f"{formatar(v, m)}\n({s:.1%})" for v, s in zip(geral[m], share)]
            else:
                rotulos = [formatar(v, m) for v in geral[m]]
            ax.bar_label(barras, labels=rotulos, fontsize=8, padding=2)
            ax.margins(y=0.2)
            ax.set_title(f"{ROTULOS[m]} — período")
            eixo(ax, m)

            ax = linha[1]
            pivo = mensal.pivot(index="mes", columns="des_canal_venda_final_agrup", values=m)[CANAIS].sort_index()
            if eh_soma(m):
                share = pivo.div(pivo.sum(axis=1), axis=0)
                base = np.zeros(len(pivo))
                for canal in CANAIS:
                    barras = ax.bar(pivo.index, pivo[canal], bottom=base, color=CORES_CANAL[canal], label=canal)
                    ax.bar_label(barras, labels=[f"{s:.0%}" for s in share[canal]], label_type="center",
                                 fontsize=7, color="white")
                    base += pivo[canal].to_numpy()
            else:
                for canal in CANAIS:
                    ax.plot(pivo.index, pivo[canal], marker="o", color=CORES_CANAL[canal], label=canal)
                    for x, v in zip(pivo.index, pivo[canal]):
                        ax.annotate(formatar(v, m), (x, v), xytext=(0, 6), textcoords="offset points",
                                    ha="center", fontsize=7, color=CORES_CANAL[canal])
                ax.margins(y=0.2)
            ax.set_title(f"{ROTULOS[m]} — mês a mês por canal")
            eixo(ax, m)
            ax.tick_params(axis="x", rotation=45)
            ax.grid(axis="y", alpha=0.3)
            ax.legend(fontsize=8)
        fig.tight_layout()
        plt.show()


    def por_categoria(self, metricas: list[str]) -> None:
        """Por categoria: à esquerda o total do período; à direita a evolução mensal.

        Soma: barras com valor e share; mês a mês empilhado (share no rótulo quando >= 5%).
        Razão: valor por categoria e linhas mês a mês.
        """
        geral = agregar(self.base, ["des_categoria_material"]).set_index("des_categoria_material")
        mensal = agregar(self.base, ["mes", "des_categoria_material"])
        fig, axes = plt.subplots(len(metricas), 2, figsize=(18, 5.5 * len(metricas)), squeeze=False,
                                 gridspec_kw={"width_ratios": [1, 1.8]})
        for linha, m in zip(axes, metricas):
            ax = linha[0]
            ordem = geral[m].reindex(self.categorias_com_invalida).sort_values()
            barras = ax.barh(ordem.index, ordem.values, color=[self.cores_com_invalida[c] for c in ordem.index])
            if eh_soma(m):
                share = ordem / ordem.sum()
                rotulos = [f"{formatar(v, m)} ({s:.1%})" for v, s in zip(ordem.values, share)]
            else:
                rotulos = [formatar(v, m) for v in ordem.values]
            ax.bar_label(barras, labels=rotulos, fontsize=7, padding=2)
            ax.margins(x=0.3)
            ax.set_title(f"{ROTULOS[m]} — período")
            eixo(ax, m, "x")

            ax = linha[1]
            pivo = (
                mensal.pivot(index="mes", columns="des_categoria_material", values=m)
                .reindex(columns=self.categorias_com_invalida).sort_index()
            )
            if eh_soma(m):
                share = pivo.div(pivo.sum(axis=1), axis=0)
                base = np.zeros(len(pivo))
                for cat in self.categorias_com_invalida:
                    barras = ax.bar(pivo.index, pivo[cat], bottom=base, color=self.cores_com_invalida[cat], label=cat)
                    ax.bar_label(barras, labels=[f"{s:.0%}" if s >= 0.05 else "" for s in share[cat]],
                                 label_type="center", fontsize=6, color="white")
                    base += pivo[cat].fillna(0).to_numpy()
            else:
                for cat in self.categorias_com_invalida:
                    ax.plot(pivo.index, pivo[cat], marker="o", markersize=3, linewidth=1.8,
                            color=self.cores_com_invalida[cat], label=cat)
            ax.set_title(f"{ROTULOS[m]} — mês a mês por categoria")
            eixo(ax, m)
            ax.tick_params(axis="x", rotation=45)
            ax.grid(axis="y", alpha=0.3)
            ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
        fig.tight_layout()
        plt.show()


    def canal_x_categoria(self, metricas: list[str]) -> None:
        """App e Site lado a lado, por categoria (mesma ordem de categorias nos dois painéis).

        Soma: valor absoluto e share da categoria dentro do canal, cada canal na sua escala
        (o Site é ~1/4 do App; o share no rótulo é o que se compara).
        Razão: valor da razão, com a mesma escala nos dois canais.
        """
        cc = agregar(self.base, ["des_canal_venda_final_agrup", "des_categoria_material"])
        fig, axes = plt.subplots(len(metricas), 2, figsize=(16, 5 * len(metricas)), squeeze=False)
        for linha, m in zip(axes, metricas):
            for ax, canal in zip(linha, CANAIS):
                serie = (
                    cc[cc["des_canal_venda_final_agrup"] == canal]
                    .set_index("des_categoria_material")[m]
                    .reindex(self.categorias_com_invalida[::-1])
                )
                barras = ax.barh(serie.index, serie.values, color=[self.cores_com_invalida[c] for c in serie.index])
                if eh_soma(m):
                    share = serie / serie.sum()
                    rotulos = [f"{formatar(v, m)} ({s:.1%})" for v, s in zip(serie.values, share)]
                else:
                    rotulos = [formatar(v, m) for v in serie.values]
                ax.bar_label(barras, labels=rotulos, fontsize=7, padding=2)
                ax.margins(x=0.3)
                ax.set_title(f"{canal} — {ROTULOS[m]} por categoria")
                eixo(ax, m, "x")
            if not eh_soma(m):
                # razões na mesma escala para comparar App x Site diretamente
                limite = max(a.get_xlim()[1] for a in linha)
                for a in linha:
                    a.set_xlim(0, limite)
        fig.tight_layout()
        plt.show()
