import time
from datetime import datetime, timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.cache import cache_path, is_cache_fresh, save_cache, load_cache

class TradingViewParser:
    def __init__(self, driver, config, logger):
        self.driver = driver
        self.config = config
        self.logger = logger

    def _wait_table(self):
        WebDriverWait(self.driver, self.config["selenium"]["timeout"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )

    def open_market(self):
        url = self.config["site"]["base_url"]
        self.logger.info("Открываем %s", url)
        self.driver.get(url)
        self._wait_table()
        self.logger.info("Таблица загружена")

    def switch_tab(self, tab_name: str):
        xpath = f"//*[contains(text(), '{tab_name}')]"
        el = WebDriverWait(self.driver, self.config["selenium"]["timeout"]).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        el.click()
        time.sleep(2)
        self._wait_table()
        self.logger.info("Переключились на вкладку: %s", tab_name)

    def _collect_rows(self, limit: int, tab_key: str) -> list[list[str]]:
        cpath = cache_path(self.config["paths"]["cache_dir"], tab_key)
        ttl = self.config["cache"]["ttl_seconds"]

        if is_cache_fresh(cpath, ttl):
            self.logger.info("Используем кэш для %s", tab_key)
            html = load_cache(cpath)
            # Быстрый путь: парсим HTML напрямую (без Selenium)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            rows = []
            for tr in soup.select("table tbody tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2:
                    rows.append(cells)
                if len(rows) >= limit:
                    break
            return rows[:limit]

        # Медленный путь: Selenium + прокрутка
        rows = []
        last_count = 0

        while len(rows) < limit:
            trs = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for tr in trs:
                if len(rows) >= limit:
                    break
                cells = tr.find_elements(By.TAG_NAME, "td")
                if len(cells) < 2:
                    continue
                row = [c.text.strip() for c in cells]
                rows.append(row)

            if len(rows) == last_count:
                # новых строк нет — прокручиваем
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(1.5)
                new_trs = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if len(new_trs) == len(trs):
                    self.logger.warning("Данные не догружаются, останавливаемся на %d строках", len(rows))
                    break

            last_count = len(rows)

        save_cache(cpath, self.driver.page_source)
        self.logger.info("Собрано %d строк (%s)", len(rows), tab_key)
        return rows[:limit]

    def parse_overview(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["overview"])
        raw = self._collect_rows(self.config["site"]["items_count"], "overview")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 8:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "price": r[1],
                "change_percent": r[2] if len(r) > 2 else "",
                "change_abs": r[3] if len(r) > 3 else "",
                "bid": r[4] if len(r) > 4 else "",
                "ask": r[5] if len(r) > 5 else "",
                "low_24h": r[6] if len(r) > 6 else "",
                "high_24h": r[7] if len(r) > 7 else "",
                "tech_rating": r[8] if len(r) > 8 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Обзор: сформировано %d записей", len(result))
        return result

    def parse_dynamics(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["dynamics"])
        raw = self._collect_rows(self.config["site"]["items_count"], "dynamics")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 2:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "change_percent_1d": r[1] if len(r) > 1 else "",
                "dynamics_1w": r[2] if len(r) > 2 else "",
                "dynamics_1m": r[3] if len(r) > 3 else "",
                "dynamics_3m": r[4] if len(r) > 4 else "",
                "dynamics_6m": r[5] if len(r) > 5 else "",
                "dynamics_1y": r[6] if len(r) > 6 else "",
                "dynamics_5y": r[7] if len(r) > 7 else "",
                "dynamics_10y": r[8] if len(r) > 8 else "",
                "dynamics_all": r[9] if len(r) > 9 else "",
                "volatility": r[10] if len(r) > 10 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Динамика: сформировано %d записей", len(result))
        return result

    def parse_tech(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["tech"])
        raw = self._collect_rows(self.config["site"]["items_count"], "tech")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 2:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "tech_rating_1d": r[1] if len(r) > 1 else "",
                "ma_rating": r[2] if len(r) > 2 else "",
                "osc_rating": r[3] if len(r) > 3 else "",
                "rsi": r[4] if len(r) > 4 else "",
                "mom": r[5] if len(r) > 5 else "",
                "cci": r[6] if len(r) > 6 else "",
                "macd_level": r[7] if len(r) > 7 else "",
                "macd_signal": r[8] if len(r) > 8 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Теханализ: сформировано %d записей", len(result))
        return resultimport time
from datetime import datetime, timezone

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.cache import cache_path, is_cache_fresh, save_cache, load_cache


class TradingViewParser:
    def __init__(self, driver, config, logger):
        self.driver = driver
        self.config = config
        self.logger = logger

    def _wait_table(self):
        WebDriverWait(self.driver, self.config["selenium"]["timeout"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )

    def open_market(self):
        url = self.config["site"]["base_url"]
        self.logger.info("Открываем %s", url)
        self.driver.get(url)
        self._wait_table()
        self.logger.info("Таблица загружена")

    def switch_tab(self, tab_name: str):
        xpath = f"//*[contains(text(), '{tab_name}')]"
        el = WebDriverWait(self.driver, self.config["selenium"]["timeout"]).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        el.click()
        time.sleep(2)
        self._wait_table()
        self.logger.info("Переключились на вкладку: %s", tab_name)

    def _collect_rows(self, limit: int, tab_key: str) -> list[list[str]]:
        cpath = cache_path(self.config["paths"]["cache_dir"], tab_key)
        ttl = self.config["cache"]["ttl_seconds"]

        if is_cache_fresh(cpath, ttl):
            self.logger.info("Используем кэш для %s", tab_key)
            html = load_cache(cpath)
            # Быстрый путь: парсим HTML напрямую (без Selenium)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            rows = []
            for tr in soup.select("table tbody tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2:
                    rows.append(cells)
                if len(rows) >= limit:
                    break
            return rows[:limit]

        # Медленный путь: Selenium + прокрутка
        rows = []
        last_count = 0

        while len(rows) < limit:
            trs = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for tr in trs:
                if len(rows) >= limit:
                    break
                cells = tr.find_elements(By.TAG_NAME, "td")
                if len(cells) < 2:
                    continue
                row = [c.text.strip() for c in cells]
                rows.append(row)

            if len(rows) == last_count:
                # новых строк нет — прокручиваем
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(1.5)
                new_trs = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if len(new_trs) == len(trs):
                    self.logger.warning("Данные не догружаются, останавливаемся на %d строках", len(rows))
                    break

            last_count = len(rows)

        # Сохраняем HTML в кэш (сырой page_source)
        save_cache(cpath, self.driver.page_source)
        self.logger.info("Собрано %d строк (%s)", len(rows), tab_key)
        return rows[:limit]

    def parse_overview(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["overview"])
        raw = self._collect_rows(self.config["site"]["items_count"], "overview")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 8:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "price": r[1],
                "change_percent": r[2] if len(r) > 2 else "",
                "change_abs": r[3] if len(r) > 3 else "",
                "bid": r[4] if len(r) > 4 else "",
                "ask": r[5] if len(r) > 5 else "",
                "low_24h": r[6] if len(r) > 6 else "",
                "high_24h": r[7] if len(r) > 7 else "",
                "tech_rating": r[8] if len(r) > 8 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Обзор: сформировано %d записей", len(result))
        return result

    def parse_dynamics(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["dynamics"])
        raw = self._collect_rows(self.config["site"]["items_count"], "dynamics")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 2:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "change_percent_1d": r[1] if len(r) > 1 else "",
                "dynamics_1w": r[2] if len(r) > 2 else "",
                "dynamics_1m": r[3] if len(r) > 3 else "",
                "dynamics_3m": r[4] if len(r) > 4 else "",
                "dynamics_6m": r[5] if len(r) > 5 else "",
                "dynamics_1y": r[6] if len(r) > 6 else "",
                "dynamics_5y": r[7] if len(r) > 7 else "",
                "dynamics_10y": r[8] if len(r) > 8 else "",
                "dynamics_all": r[9] if len(r) > 9 else "",
                "volatility": r[10] if len(r) > 10 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Динамика: сформировано %d записей", len(result))
        return result

    def parse_tech(self) -> list[dict]:
        self.switch_tab(self.config["site"]["tabs"]["tech"])
        raw = self._collect_rows(self.config["site"]["items_count"], "tech")

        result = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in raw:
            if len(r) < 2:
                continue
            result.append({
                "pair_id": r[0].replace("/", "").replace(" ", "").upper(),
                "name": r[0],
                "tech_rating_1d": r[1] if len(r) > 1 else "",
                "ma_rating": r[2] if len(r) > 2 else "",
                "osc_rating": r[3] if len(r) > 3 else "",
                "rsi": r[4] if len(r) > 4 else "",
                "mom": r[5] if len(r) > 5 else "",
                "cci": r[6] if len(r) > 6 else "",
                "macd_level": r[7] if len(r) > 7 else "",
                "macd_signal": r[8] if len(r) > 8 else "",
                "timestamp": now_iso,
            })
        self.logger.info("Теханализ: сформировано %d записей", len(result))
        return result
