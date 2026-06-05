import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_KEY"]
RETENCAO_DIAS = 90


def run() -> None:
    corte = (datetime.now(timezone.utc) - timedelta(days=RETENCAO_DIAS)).strftime("%Y-%m-%dT%H:%M:%S")

    logger.info("Removendo registros anteriores a %s (%d dias de retenção)", corte, RETENCAO_DIAS)

    try:
        client   = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table("cotacoes").delete().lt("collected_at", corte).execute()
        removidos = len(response.data) if response.data else 0
        logger.info("Limpeza concluída: %d registros removidos", removidos)
    except Exception:
        logger.exception("Falha na limpeza — abortando")
        sys.exit(1)


if __name__ == "__main__":
    run()
