"""Consultas SQL do projeto: leitura dos arquivos em sql/ e execução no BigQuery."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .bigquery import estimate_query_bytes, read_query


def encontrar_pasta_sql(inicio: str | Path | None = None) -> Path:
    """Sobe a partir de `inicio` (padrão: diretório atual) até achar a pasta sql/ do projeto."""
    inicio = Path(inicio or Path.cwd()).resolve()
    for pasta in [inicio, *inicio.parents]:
        if (pasta / "sql").is_dir():
            return pasta / "sql"
    raise FileNotFoundError(f"pasta sql/ não encontrada a partir de {inicio}")


class ConsultasBQ:
    """Lê sql/<arquivo>, preenche os parâmetros e roda no BigQuery com dry-run antes.

    Parâmetros fixos (tabela, período etc.) vêm da configuração do notebook; os
    específicos de uma consulta (ex.: condicao_sql) são passados em `carregar`.
    """

    def __init__(self, project_id: str, location: str, parametros: dict[str, str],
                 pasta_sql: str | Path | None = None):
        self.project_id = project_id
        self.location = location
        self.parametros = parametros
        self.pasta_sql = Path(pasta_sql) if pasta_sql else encontrar_pasta_sql()

    def carregar(self, arquivo: str, **parametros) -> str:
        modelo = (self.pasta_sql / arquivo).read_text(encoding="utf-8")
        return modelo.format(**self.parametros, **parametros)

    def rodar(self, sql: str, label: str | None = None) -> pd.DataFrame:
        bytes_processed = estimate_query_bytes(sql, project_id=self.project_id, location=self.location)
        mb = bytes_processed / 1024**2
        print(f"[BigQuery] {label or 'query'} | estimativa processada: {mb:,.2f} MB")
        return read_query(sql, project_id=self.project_id, location=self.location)
