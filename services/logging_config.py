import logging
from pathlib import Path

ASSETS = Path("assets")
log_path = ASSETS / "app.log"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers = [
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )