import csv
import os
from datetime import datetime
from src.config_loader import load_config
from src.logger import setup_loggers
from src.driver_factory import create_driver
from src.tradingview_parser import TradingViewParser

def save_csv(rows: list[dict], fieldnames: list[str], data_dir: str, filename: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(data_dir, date_str)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CSV] {filename}: {len(rows)} записей → {filepath}")


def main():
    config = load_config("config.yaml")
    logger = setup_loggers(config["paths"]["logs_dir"])
    driver = create_driver(config)
    parser = TradingViewParser(driver, config, logger)

    try:
        logger.info("===== СТАРТ СБОРА ДАННЫХ =====")
        parser.open_market()

        # ---- Обзор ----
        overview = parser.parse_overview()
        save_csv(
            overview,
            ["pair_id", "name", "price", "change_percent", "change_abs",
             "bid", "ask", "low_24h", "high_24h", "tech_rating", "timestamp"],
            config["paths"]["data_dir"],
            "Обзор.csv",
        )

        # ---- Динамика ----
        dynamics = parser.parse_dynamics()
        save_csv(
            dynamics,
            ["pair_id", "name", "change_percent_1d", "dynamics_1w", "dynamics_1m",
             "dynamics_3m", "dynamics_6m", "dynamics_1y", "dynamics_5y",
             "dynamics_10y", "dynamics_all", "volatility", "timestamp"],
            config["paths"]["data_dir"],
            "Динамика.csv",
        )

        # ---- Теханализ ----
        tech = parser.parse_tech()
        save_csv(
            tech,
            ["pair_id", "name", "tech_rating_1d", "ma_rating", "osc_rating",
             "rsi", "mom", "cci", "macd_level", "macd_signal", "timestamp"],
            config["paths"]["data_dir"],
            "Теханализ.csv",
        )

        logger.info("===== СБОР ЗАВЕРШЁН =====")

    except Exception as e:
        logger.error("Критическая ошибка: %s", e, exc_info=True)
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
