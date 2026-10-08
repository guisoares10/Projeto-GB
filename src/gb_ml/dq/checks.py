"""Checks genéricos de qualidade de dados e quality gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


import numpy as np
import pandas as pd

from gb_ml.profiling.profile import profile_dataframe


@dataclass(frozen=True)
class CheckResult:
    check: str
    coluna: str | None
    status: str
    severidade: str
    metrica: float | int | str | None
    limite: float | int | str | None
    detalhe: str


def _result(
    check: str,
    *,
    coluna: str | None = None,
    status: str,
    severidade: str = "warn",
    metrica: float | int | str | None = None,
    limite: float | int | str | None = None,
    detalhe: str = "",
) -> CheckResult:
    return CheckResult(check, coluna, status, severidade, metrica, limite, detalhe)


def run_quality_checks(df: pd.DataFrame, config: dict[str, Any] | None = None) -> pd.DataFrame:
    """Executa checks automáticos e checks guiados por configuração."""
    config = config or {}
    defaults = config.get("defaults", {})
    columns_cfg = config.get("columns", {})
    grain = config.get("grain", [])

    warn_null_pct = float(defaults.get("warn_null_pct", 0.05))
    error_null_pct = float(defaults.get("error_null_pct", 0.30))
    warn_blank_pct = float(defaults.get("warn_blank_pct", 0.01))

    results: list[CheckResult] = []
    n_rows = len(df)

    duplicated_rows = int(df.duplicated().sum())
    results.append(
        _result(
            "duplicidade_linha",
            status="fail" if duplicated_rows else "pass",
            severidade="warn",
            metrica=duplicated_rows,
            limite=0,
            detalhe="Linhas completamente duplicadas.",
        )
    )

    if grain:
        missing_keys = [c for c in grain if c not in df.columns]
        if missing_keys:
            results.append(
                _result(
                    "grao_colunas_ausentes",
                    status="fail",
                    severidade="error",
                    metrica=",".join(missing_keys),
                    limite="todas presentes",
                    detalhe="Colunas necessárias para validar o grão não existem.",
                )
            )
        else:
            dup_grain = int(df.duplicated(subset=grain, keep=False).sum())
            results.append(
                _result(
                    "grao_unico",
                    status="fail" if dup_grain else "pass",
                    severidade="error",
                    metrica=dup_grain,
                    limite=0,
                    detalhe=f"Linhas envolvidas em duplicidade no grão {grain}.",
                )
            )

    profile = profile_dataframe(df)

    for _, row in profile.iterrows():
        col = str(row["coluna"])
        null_pct = float(row["pct_nulos"])
        blank_pct = float(row["vazios_string"]) / n_rows if n_rows else 0.0

        explicit = columns_cfg.get(col, {})
        nullable = explicit.get("nullable")
        null_limit = explicit.get("max_null_pct")

        if nullable is False:
            allowed = float(null_limit if null_limit is not None else 0.0)
            status = "fail" if null_pct > allowed else "pass"
            severity = "error"
            limit = allowed
        else:
            if null_limit is not None:
                limit = float(null_limit)
                status = "fail" if null_pct > limit else "pass"
                severity = str(explicit.get("null_severity", "warn"))
            elif null_pct >= error_null_pct:
                limit = error_null_pct
                status = "fail"
                severity = "error"
            elif null_pct >= warn_null_pct:
                limit = warn_null_pct
                status = "fail"
                severity = "warn"
            else:
                limit = warn_null_pct
                status = "pass"
                severity = "warn"

        results.append(
            _result(
                "nulos",
                coluna=col,
                status=status,
                severidade=severity,
                metrica=round(null_pct, 6),
                limite=limit,
                detalhe="Proporção de valores nulos.",
            )
        )

        if blank_pct > 0:
            results.append(
                _result(
                    "string_vazia",
                    coluna=col,
                    status="fail" if blank_pct >= warn_blank_pct else "pass",
                    severidade="warn",
                    metrica=round(blank_pct, 6),
                    limite=warn_blank_pct,
                    detalhe="Strings vazias ou compostas apenas por espaços.",
                )
            )

        if bool(row["constante"]):
            results.append(
                _result(
                    "coluna_constante",
                    coluna=col,
                    status="fail",
                    severidade="warn",
                    metrica=int(row["unicos"]),
                    limite=">1",
                    detalhe="Coluna sem variabilidade; pode não agregar sinal ao modelo.",
                )
            )

        candidate = row["tipo_candidato"]
        if pd.notna(candidate) and candidate:
            results.append(
                _result(
                    "tipo_suspeito",
                    coluna=col,
                    status="fail",
                    severidade="warn",
                    metrica=f"{float(row['taxa_conversao_tipo']):.1%}",
                    limite="dtype coerente",
                    detalhe=f"Coluna armazenada como {row['dtype']} parece ser {candidate}.",
                )
            )

    for col in df.select_dtypes(include=np.number).columns:
        s = pd.to_numeric(df[col], errors="coerce")
        inf_count = int(np.isinf(s.to_numpy(dtype=float, na_value=np.nan)).sum())
        if inf_count:
            results.append(
                _result(
                    "valores_infinitos",
                    coluna=str(col),
                    status="fail",
                    severidade="error",
                    metrica=inf_count,
                    limite=0,
                    detalhe="Valores +inf/-inf não são aceitos no dataset de modelagem.",
                )
            )

    for col, rules in columns_cfg.items():
        if col not in df.columns:
            results.append(
                _result(
                    "coluna_obrigatoria",
                    coluna=col,
                    status="fail",
                    severidade=str(rules.get("missing_severity", "error")),
                    metrica="ausente",
                    limite="presente",
                    detalhe="Coluna definida no contrato não foi encontrada.",
                )
            )
            continue

        s = df[col]
        expected_type = rules.get("type")
        if expected_type:
            ok = _dtype_matches(s, str(expected_type))
            results.append(
                _result(
                    "tipo_contrato",
                    coluna=col,
                    status="pass" if ok else "fail",
                    severidade=str(rules.get("type_severity", "error")),
                    metrica=str(s.dtype),
                    limite=str(expected_type),
                    detalhe="Compatibilidade entre dtype observado e tipo esperado.",
                )
            )

        if "min" in rules or "max" in rules:
            numeric = pd.to_numeric(s, errors="coerce")
            if "min" in rules:
                invalid = int((numeric < rules["min"]).fillna(False).sum())
                results.append(
                    _result(
                        "limite_minimo",
                        coluna=col,
                        status="fail" if invalid else "pass",
                        severidade=str(rules.get("bounds_severity", "error")),
                        metrica=invalid,
                        limite=rules["min"],
                        detalhe="Quantidade de valores abaixo do mínimo permitido.",
                    )
                )
            if "max" in rules:
                invalid = int((numeric > rules["max"]).fillna(False).sum())
                results.append(
                    _result(
                        "limite_maximo",
                        coluna=col,
                        status="fail" if invalid else "pass",
                        severidade=str(rules.get("bounds_severity", "error")),
                        metrica=invalid,
                        limite=rules["max"],
                        detalhe="Quantidade de valores acima do máximo permitido.",
                    )
                )

        allowed_values = rules.get("allowed_values")
        if allowed_values is not None:
            invalid = int((~s.isna() & ~s.isin(allowed_values)).sum())
            results.append(
                _result(
                    "dominio_categorico",
                    coluna=col,
                    status="fail" if invalid else "pass",
                    severidade=str(rules.get("domain_severity", "error")),
                    metrica=invalid,
                    limite=f"{len(allowed_values)} valores permitidos",
                    detalhe="Valores fora do domínio categórico configurado.",
                )
            )

        if rules.get("date_no_future"):
            parsed = pd.to_datetime(s, errors="coerce")
            now = pd.Timestamp.now(tz=None).normalize()
            future = int((parsed > now).fillna(False).sum())
            results.append(
                _result(
                    "data_futura",
                    coluna=col,
                    status="fail" if future else "pass",
                    severidade=str(rules.get("future_severity", "error")),
                    metrica=future,
                    limite=0,
                    detalhe="Datas futuras em coluna que deveria representar fatos observados.",
                )
            )

    return pd.DataFrame([asdict(r) for r in results])


def _dtype_matches(series: pd.Series, expected: str) -> bool:
    expected = expected.lower()
    if expected in {"number", "numeric", "float", "integer", "int"}:
        return pd.api.types.is_numeric_dtype(series)
    if expected in {"date", "datetime", "timestamp"}:
        return pd.api.types.is_datetime64_any_dtype(series)
    if expected in {"string", "text", "category", "categorical"}:
        return (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
            or isinstance(series.dtype, pd.CategoricalDtype)
        )
    if expected in {"bool", "boolean"}:
        return pd.api.types.is_bool_dtype(series)
    return str(series.dtype).lower() == expected


def quality_gate(report: pd.DataFrame) -> tuple[bool, pd.DataFrame]:
    """Retorna (aprovado, falhas_críticas)."""
    if report.empty:
        return True, report.copy()
    critical = report[(report["status"] == "fail") & (report["severidade"] == "error")].copy()
    return critical.empty, critical
