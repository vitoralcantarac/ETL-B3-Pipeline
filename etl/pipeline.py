import logging
import os
import sys

from etl.extract import extract
from etl.transform import transform
from etl.load import load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

VARS_OBRIGATORIAS = ["BRAPI_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"]


def validar_env() -> None:
    ausentes = [v for v in VARS_OBRIGATORIAS if not os.environ.get(v)]
    if ausentes:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias ausentes: {', '.join(ausentes)}\n"
            f"Configure o arquivo .env ou os Secrets do GitHub Actions."
        )


def run() -> None:
    try:
        validar_env()
    except EnvironmentError as e:
        logger.error("Configuração inválida — %s", e)
        sys.exit(1)

    logger.info("Pipeline iniciada")

    try:
        raw = extract()
    except Exception:
        logger.exception("Falha na extração — abortando pipeline")
        sys.exit(1)

    try:
        df = transform(raw)
    except Exception:
        logger.exception("Falha na transformação — abortando pipeline")
        sys.exit(1)

    if df.empty:
        logger.warning("Nenhum dado válido para carregar — encerrando sem erro")
        return

    try:
        load(df)
    except Exception:
        logger.exception("Falha na carga — abortando pipeline")
        sys.exit(1)

    logger.info("Pipeline finalizada com sucesso")


if __name__ == "__main__":
    run()
