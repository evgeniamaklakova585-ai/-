import logging
import os

def setup_loggers(logs_dir: str):
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "tradingview_scraper.log")

    logger = logging.getLogger("tradingview_scraper")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    return logger
