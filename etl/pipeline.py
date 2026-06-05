import logging
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


def run() -> None:
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
