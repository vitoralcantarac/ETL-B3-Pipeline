import logging
import os

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def load(df: pd.DataFrame) -> None:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    records = df.to_dict(orient="records")

    # upsert com on_conflict ignora silenciosamente duplicatas na mesma hora
    response = (
        client.table("cotacoes")
        .upsert(records, on_conflict="symbol,collected_at")
        .execute()
    )

    logger.info("%d registros enviados ao Supabase", len(records))
    return response
