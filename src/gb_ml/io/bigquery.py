"""Utilitários seguros e econômicos para leitura do BigQuery."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

def _client(
    project_id: str | None = None,
    *,
    location: str | None = None,
):
    """Cria client do BigQuery com projeto e região opcionais."""
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise ImportError(
            "Instale as dependências de BigQuery com: pip install -e '.[bq]'"
        ) from exc

    return bigquery.Client(
        project=project_id,
        location=location,
    )


def estimate_query_bytes(
    sql: str,
    *,
    project_id: str | None = None,
    location: str | None = None,
) -> int:
    """Faz dry-run e retorna os bytes que a query processaria."""
    from google.cloud import bigquery

    client = _client(project_id, location=location)
    job_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
    )
    job = client.query(
        sql,
        job_config=job_config,
        location=location,
    )
    return int(job.total_bytes_processed or 0)


def read_query(
    sql: str,
    *,
    project_id: str | None = None,
    location: str | None = None,
    maximum_bytes_billed: int | None = None,
) -> pd.DataFrame:
    """Executa query e retorna DataFrame, com região e limite de bytes opcionais."""
    from google.cloud import bigquery

    client = _client(project_id, location=location)
    job_config = bigquery.QueryJobConfig()

    if maximum_bytes_billed is not None:
        job_config.maximum_bytes_billed = int(maximum_bytes_billed)

    return client.query(
        sql,
        job_config=job_config,
        location=location,
    ).to_dataframe()


def table_metadata(
    table_id: str,
    *,
    project_id: str | None = None,
    location: str | None = None,
) -> tuple[dict, pd.DataFrame]:
    """Retorna metadados gerais e schema de uma tabela."""
    client = _client(project_id, location=location)
    table = client.get_table(table_id)

    metadata = {
        "table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
        "num_rows": int(table.num_rows or 0),
        "num_bytes": int(table.num_bytes or 0),
        "created": table.created,
        "modified": table.modified,
        "location": location or client.location,
        "partitioning_type": (
            type(table.time_partitioning).__name__
            if table.time_partitioning
            else None
        ),
        "partition_field": (
            table.time_partitioning.field
            if table.time_partitioning
            else None
        ),
        "clustering_fields": list(table.clustering_fields or []),
    }

    schema = pd.DataFrame(
        [
            {
                "name": field.name,
                "field_type": field.field_type,
                "mode": field.mode,
                "description": field.description,
            }
            for field in table.schema
        ]
    )
    return metadata, schema


def sample_table(
    table_id: str,
    *,
    limit: int = 100_000,
    columns: Iterable[str] | None = None,
    where: str | None = None,
    project_id: str | None = None,
    location: str | None = None,
    maximum_bytes_billed: int | None = None,
) -> pd.DataFrame:
    """Carrega uma amostra explícita de uma tabela para análise local."""
    if limit <= 0:
        raise ValueError("limit deve ser maior que zero")

    selected = "*" if not columns else ", ".join(f"`{c}`" for c in columns)
    sql = f"SELECT {selected} FROM `{table_id}`"

    if where:
        sql += f" WHERE {where}"

    sql += f" LIMIT {int(limit)}"

    return read_query(
        sql,
        project_id=project_id,
        location=location,
        maximum_bytes_billed=maximum_bytes_billed,
    )
