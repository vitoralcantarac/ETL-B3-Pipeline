import re

import pandas as pd
import pytest

from etl.transform import transform


# ── fixtures ────────────────────────────────────────────────────────────────

def make_item(**overrides) -> dict:
    """Retorna um item padrão da brapi.dev com possibilidade de override."""
    base = {
        "symbol": "PETR4",
        "regularMarketPrice": 38.42,
        "regularMarketChange": 0.47,
        "regularMarketChangePercent": 1.24,
        "regularMarketVolume": 42_300_000,
        "marketCap": 493_800_000_000,
    }
    base.update(overrides)
    return base


# ── caso feliz ───────────────────────────────────────────────────────────────

def test_transform_retorna_dataframe():
    df = transform([make_item()])
    assert isinstance(df, pd.DataFrame)


def test_transform_colunas_corretas():
    df = transform([make_item()])
    esperadas = {"symbol", "price", "change", "change_pct", "volume", "market_cap", "collected_at"}
    assert set(df.columns) == esperadas


def test_transform_valores_corretos():
    df = transform([make_item()])
    row = df.iloc[0]
    assert row["symbol"] == "PETR4"
    assert float(row["price"]) == pytest.approx(38.42)
    assert float(row["change_pct"]) == pytest.approx(1.24)


def test_transform_multiplos_ativos():
    items = [make_item(symbol="PETR4"), make_item(symbol="VALE3"), make_item(symbol="MXRF11")]
    df = transform(items)
    assert len(df) == 3
    assert set(df["symbol"]) == {"PETR4", "VALE3", "MXRF11"}


# ── collected_at ─────────────────────────────────────────────────────────────

def test_collected_at_truncado_na_hora():
    """Minutos e segundos devem ser sempre :00:00 para garantir idempotência."""
    df = transform([make_item()])
    collected_at = df.iloc[0]["collected_at"]
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:00:00$", collected_at), (
        f"collected_at fora do formato esperado: {collected_at}"
    )


# ── validação de dados ───────────────────────────────────────────────────────

def test_ativo_sem_preco_e_ignorado():
    items = [make_item(symbol="PETR4", regularMarketPrice=None), make_item(symbol="VALE3")]
    df = transform(items)
    assert len(df) == 1
    assert df.iloc[0]["symbol"] == "VALE3"


def test_lista_vazia_retorna_dataframe_vazio():
    df = transform([])
    assert df.empty


def test_todos_sem_preco_retorna_dataframe_vazio():
    items = [make_item(regularMarketPrice=None), make_item(regularMarketPrice=None)]
    df = transform(items)
    assert df.empty


# ── tipos e serialização ──────────────────────────────────────────────────────

def test_tipos_numericos_corretos():
    df = transform([make_item()])
    assert pd.api.types.is_float_dtype(df["price"])
    assert pd.api.types.is_float_dtype(df["change"])
    assert pd.api.types.is_float_dtype(df["change_pct"])


def test_volume_market_cap_sem_valores_nulos_pd_na():
    """pd.NA não serializa para JSON — deve ser convertido para None."""
    items = [make_item(regularMarketVolume=None, marketCap=None)]
    df = transform(items)
    row = df.iloc[0]
    # to_dict deve produzir None, não pd.NA
    record = df.to_dict(orient="records")[0]
    assert record["volume"] is None
    assert record["market_cap"] is None


def test_valores_string_invalidos_viram_none():
    """API poderia retornar string inválida — deve ser tratada com errors='coerce'."""
    items = [make_item(regularMarketVolume="N/A", marketCap="—")]
    df = transform(items)
    record = df.to_dict(orient="records")[0]
    assert record["volume"] is None
    assert record["market_cap"] is None
