import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BRAPI_TOKEN = os.environ["BRAPI_TOKEN"]

TICKERS = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MGLU3", "MXRF11", "HGLG11", "KNRI11"]


def extract() -> list[dict]:
    results = []
    for ticker in TICKERS:
        url = f"https://brapi.dev/api/quote/{ticker}?token={BRAPI_TOKEN}"
        logger.info("Coletando %s da brapi.dev", ticker)
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        results.extend(response.json().get("results", []))
        time.sleep(0.5)

    logger.info("%d ativos retornados pela API", len(results))
    return results
