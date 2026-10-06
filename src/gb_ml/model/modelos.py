"""Modelos da previsão de qt_material, no formato ajustar_prever(treino, teste).

Cada fábrica recebe os hiperparâmetros e devolve a função usada no backtest.
O alvo pode ser modelado em log (log1p, efeitos multiplicativos), em nível
(regressão linear) ou com objetivo Poisson (árvores, alvo de contagem).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from gb_ml.features.vendas import ALVO, matriz_arvore, matriz_linear

from .backtest import AjustarPrever


def _alvo(y: pd.Series, alvo: str) -> pd.Series:
    return np.log1p(y) if alvo == "log" else y


def _volta(previsto: np.ndarray, alvo: str) -> np.ndarray:
    return np.expm1(previsto) if alvo == "log" else previsto


def ajustar_linear(treino: pd.DataFrame, alvo: str = "log", interacao: bool = False):
    """Ajusta a regressão linear (OLS, erros robustos HC1) e devolve o resultado do statsmodels."""
    import statsmodels.api as sm

    X = matriz_linear(treino, interacao)
    # evento que ainda não aconteceu no treino (coluna toda zero) fica de fora
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    return sm.OLS(_alvo(treino[ALVO], alvo), X).fit(cov_type="HC1")


def linear(alvo: str = "log", interacao: bool = False) -> AjustarPrever:
    import statsmodels.api as sm

    def ajustar_prever(treino: pd.DataFrame, teste: pd.DataFrame) -> np.ndarray:
        modelo = ajustar_linear(treino, alvo, interacao)
        X = sm.add_constant(matriz_linear(teste, interacao), has_constant="add")
        return _volta(modelo.predict(X[modelo.params.index]).to_numpy(), alvo)

    return ajustar_prever


def criar_lightgbm(alvo: str = "log", **parametros):
    import lightgbm as lgb

    objetivo = "poisson" if alvo == "poisson" else "regression"
    return lgb.LGBMRegressor(objective=objetivo, random_state=42, verbose=-1, **parametros)


def criar_xgboost(alvo: str = "log", **parametros):
    import xgboost as xgb

    objetivo = "count:poisson" if alvo == "poisson" else "reg:squarederror"
    return xgb.XGBRegressor(objective=objetivo, random_state=42, n_jobs=4, **parametros)


def arvore(
    biblioteca: str, alvo: str = "log", usar_lags: bool = True, **parametros
) -> AjustarPrever:
    """LightGBM ou XGBoost; `parametros` vão direto para o regressor."""
    criar = {"lightgbm": criar_lightgbm, "xgboost": criar_xgboost}[biblioteca]

    def ajustar_prever(treino: pd.DataFrame, teste: pd.DataFrame) -> np.ndarray:
        modelo = criar(alvo, **parametros)
        modelo.fit(matriz_arvore(treino, usar_lags), _alvo(treino[ALVO], alvo))
        return _volta(modelo.predict(matriz_arvore(teste, usar_lags)), alvo)

    return ajustar_prever


def lightgbm(**parametros) -> AjustarPrever:
    return arvore("lightgbm", **parametros)


def xgboost(**parametros) -> AjustarPrever:
    return arvore("xgboost", **parametros)
