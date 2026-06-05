import logging
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)


def transform(raw_results: list[dict]) -> pd.DataFrame:
    records = []
    for item in raw_results:
        symbol = item.get("symbol", "DESCONHECIDO")
        price = item.get("regularMarketPrice")

        if price is None:
            logger.warning("Ativo %s sem preço — ignorado", symbol)
            continue

        records.append({
            "symbol":       symbol,
            "price":        item.get("regularMarketPrice"),
            "change":       item.get("regularMarketChange"),
            "change_pct":   item.get("regularMarketChangePercent"),
            "volume":       item.get("regularMarketVolume"),
            "market_cap":   item.get("marketCap"),
            "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00:00"),
        })

    df = pd.DataFrame(records)

    if df.empty:
        return df

    df["price"]      = pd.to_numeric(df["price"],      errors="coerce")
    df["change"]     = pd.to_numeric(df["change"],     errors="coerce")
    df["change_pct"] = pd.to_numeric(df["change_pct"], errors="coerce")
    df["volume"]     = pd.to_numeric(df["volume"],     errors="coerce").astype("Int64")
    df["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce").astype("Int64")

    # Converte pd.NA → None para serialização JSON correta no Supabase
    df = df.where(df.notna(), other=None)

    logger.info("Transformação concluída: %d ativos válidos, shape %s", len(df), df.shape)
    return df
