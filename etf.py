import os
import json
import time
import yfinance as yf
import pandas as pd

from etfpy import ETF, load_etf, get_available_etfs_list

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

import logging

# Suppress logging from Selenium and other related modules
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("http").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


cwd = os.getcwd()


class Etf:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()

        self.chrome_driver_path = self._get_chrome_driver_path()
        self.base_export_path = self._get_data_export_path()
        os.makedirs(self.base_export_path, exist_ok=True)  # Create folder for ROIC data
        self.holdings_url = "https://www.schwab.wallst.com/schwab/Prospect/research/etfs/schwabETF/index.asp?type=holdings&symbol={}"

        """ -- Chromedriver options -- """
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--disable-gpu")

        # Fill in data for etf.
        self.holdings = self.get_holdings()

    """-----------------------------------"""

    def _get_data_export_path(self):
        try:
            internal_path = f"{os.getcwd()}\\config.json"
            with open(internal_path, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            external_path = f"{os.getcwd()}\\EtfCompare\\config.json"
            with open(external_path, "r") as file:
                data = json.load(file)
        return data["data_export_path"]

    """-----------------------------------"""
    """----------------------------------- Browser Operations -----------------------------------"""

    def _get_chrome_driver_path(self):
        try:
            internal_path = f"{os.getcwd()}\\config.json"
            with open(internal_path, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            external_path = f"{os.getcwd()}\\EtfCompare\\config.json"
            with open(external_path, "r") as file:
                data = json.load(file)
        return data["chrome_driver_path"]

    def _create_browser(self, url=None):
        """
        :param url: The website to visit.
        :return: None
        """
        service = Service(executable_path=self.chrome_driver_path)
        self.browser = webdriver.Chrome(service=service, options=self.chrome_options)
        # Default browser route
        if url == None:
            self.browser.get(url=self.sec_annual_url)
        # External browser route
        else:
            self.browser.get(url=url)

    def _clean_close(self) -> None:
        self.browser.close()
        self.browser.quit()

    def _read_data(
        self, xpath: str, wait: bool = False, _wait_time: int = 5, tag: str = ""
    ) -> str:
        """
        :param xpath: Path to the web element.
        :param wait: Boolean to determine if selenium should wait until the element is located.
        :param wait_time: Integer that represents how many seconds selenium should wait, if wait is True.
        :return: (str) Text of the element.
        """

        if wait:
            try:
                data = (
                    WebDriverWait(self.browser, _wait_time)
                    .until(EC.presence_of_element_located((By.XPATH, xpath)))
                    .text
                )
            except TimeoutException:
                print(f"[Failed Xpath] {xpath}")
                if tag != "":
                    print(f"[Tag]: {tag}")
                raise NoSuchElementException("Element not found")
            except NoSuchElementException:
                print(f"[Failed Xpath] {xpath}")
                return "N\A"
        else:
            try:
                data = self.browser.find_element("xpath", xpath).text
            except NoSuchElementException:
                data = "N\A"
        # Return the text of the element found.
        return data

    def _click_button(
        self,
        xpath: str,
        wait: bool = False,
        _wait_time: int = 5,
        scroll: bool = False,
        tag: str = "",
    ) -> None:
        """
        :param xpath: Path to the web element.
        :param wait: Boolean to determine if selenium should wait until the element is located.
        :param wait_time: Integer that represents how many seconds selenium should wait, if wait is True.
        :return: None. Because this function clicks the button but does not return any information about the button or any related web elements.
        """

        if wait:
            try:
                element = WebDriverWait(self.browser, _wait_time).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                # If the webdriver needs to scroll before clicking the element.
                if scroll:
                    self.browser.execute_script("arguments[0].click();", element)
                element.click()
            except TimeoutException:
                print(f"[Failed Xpath] {xpath}")
                if tag != "":
                    print(f"[Tag]: {tag}")
                raise NoSuchElementException("Element not found")
        else:
            element = self.browser.find_element("xpath", xpath)
            if scroll:
                self.browser.execute_script("arguments[0].click();", element)
            element.click()

    """----------------------------------- ETF Operations -----------------------------------"""

    def get_holdings(self):
        """
        Get holdings of an ETF.
        Will try to read data locally first.
        If it does not exist locally, it will scrape new data, and save it in the respective folder.
        """

        # Make a directory for the ETF if one does not exist.
        etf_folder = f"{self.base_export_path}\\{self.ticker}"
        holdings_file = f"{etf_folder}\\holdings.csv"
        os.makedirs(etf_folder, exist_ok=True)
        try:

            df = pd.read_csv(holdings_file)
            df.set_index("symbol", inplace=True)
            return df
        except FileNotFoundError:
            df = self._scrape_holdings()
            df.to_csv(holdings_file)
            return df

    def get_dividends(
        self,
        close: pd.Series,
        dividends: pd.Series,
        quarterly: bool = True,
        biannual: bool = False,
        monthly: bool = False,
    ):

        d_index = 0
        d_indexes = {}
        prev_timestamp = dividends.index[0]
        sections = []
        # Search indexes where a dividend occurs.
        for i in range(len(dividends)):
            current_timestamp = dividends.index[i]
            d = dividends.iloc[d_index]
            if d > 0:
                d_indexes[dividends.index[i]] = d.item()
                data = {
                    "start": prev_timestamp,
                    "end": current_timestamp,
                    "value": d.item(),
                }
                sections.append(data)
                prev_timestamp = current_timestamp
            d_index += 1

        # Add last section.
        sections.append(
            {
                "start": sections[-1]["end"],
                "end": dividends.index[-1],
                "value": sections[-1]["value"],
            }
        )
        df = pd.DataFrame(index=dividends.index, columns=["close", "dividend"])
        df["close"] = close
        df.index = pd.to_datetime(df.index)
        # df.index = pd.to_datetime(df.index)
        for s in sections:
            df.loc[s["start"] : s["end"], "dividend"] = s["value"]

        # Calculate the yield
        df["close"] = close
        df["yield"] = (df["dividend"] / df["close"]) * 100

        if quarterly:
            df["annual_yield"] = df["yield"] * 4
        elif biannual:
            df["annual_yield"] = df["yield"] * 2
        elif monthly:
            df["annual_yield"] = df["yield"] * 12
        # No parameter is chosen, default to quarterly, since that is the frequency of the majority of companies.
        else:
            df["annual_yield"] = df["yield"] * 4
        return df

    """----------------------------------- Scraping Operations -----------------------------------"""

    def _scrape_holdings(self):
        # Button to display 60 rows in the table.
        display_60_elements_button_xpath = "/html/body/div[1]/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/div/ul[1]/li[4]"
        # Xpath for "Next Page" button.
        next_path_xpath = "/html/body/div[1]/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/div/ul[2]/li[7]/a"
        # next_path_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/div/ul[2]/li[6]/a"
        # Controls which page number the scraper is on.
        page_num = 3
        page_num_xpath = "/html/body/div[1]/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/div/ul[2]/li[{}]/a"
        # Booleans to control loop.
        elements_available = True

        self._create_browser(self.holdings_url.format(self.ticker))
        """
        Logic Here 
        """
        # Display 60 rows of data.
        tickers = []

        self._scrape_table()
        page_data = {}
        cur_page = 1
        index = 0
        while elements_available:
            # This button only needs to be clicked on the first iteration.
            if index == 0:
                self._click_button(display_60_elements_button_xpath, wait=True)
                time.sleep(1)

            tickers = self._scrape_table()
            page_data[cur_page] = tickers

            # CLick the "Next Page" button.
            if page_num % 7 == 0:
                try:
                    self._click_button(next_path_xpath)
                    page_num = 2
                    cur_page += 1
                    time.sleep(1)
                except NoSuchElementException:
                    elements_available = False
            else:
                try:
                    self._click_button(page_num_xpath.format(page_num))
                    page_num += 1
                    cur_page += 1
                    time.sleep(1)
                except NoSuchElementException:
                    elements_available = False

            index += 1
        # Consolidate data from all pages into one list.
        consolidated_data = []

        for key, value in page_data.items():
            for v in value:
                consolidated_data.append(v)
        df = pd.DataFrame(consolidated_data)
        df.drop_duplicates(inplace=True)
        df.set_index("symbol", inplace=True)
        self._clean_close()

        return df

    def _scrape_table(self):
        symbol_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[{}]/td[1]"
        name_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[{}]/td[2]/span"
        weight_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[{}]/td[3]"
        shares_held_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[{}]/td[4]"
        market_value_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[{}]/td[5]"
        market_value_xpath = "/html/body/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/div/table/tbody/tr[1]/td[5]"
        scraping = True
        row_index = 1

        tickers = []
        while scraping:

            try:
                symbol = self._read_data(symbol_xpath.format(row_index), wait=True)
                name = self._read_data(name_xpath.format(row_index), wait=True)
                weight = self._read_data(weight_xpath.format(row_index), wait=True)
                shares_held = self._read_data(
                    shares_held_xpath.format(row_index), wait=True
                )
                market_value = self._read_data(
                    market_value_xpath.format(row_index), wait=True
                )
                data = {
                    "symbol": symbol,
                    "name": name,
                    "weight": weight,
                    "shares_held": self._format_value(shares_held),
                    "market_value": self._format_value(market_value),
                }
                tickers.append(data)
            except NoSuchElementException:
                scraping = False
            except StaleElementReferenceException:
                scraping = False

            row_index += 1
        return tickers

    """----------------------------------- Formatting Operations -----------------------------------"""

    def _format_value(self, value):
        # Get the magnitude of the value (B = billions, etc. )
        magnitude = value[-1]

        # Remove dollar sign and magnitude
        if value[0] == "$":
            value = value[1:-1]
        else:
            value = value[:-1]
        # Convert value to float
        value = float(value)

        if magnitude == "K":
            multiplier = 1_000
        elif magnitude == "M":
            multiplier = 1_000_000
        elif magnitude == "B":
            multiplier = 1_000_000_000
        else:
            multiplier = 1
        new_value = value * multiplier
        return new_value

    # t = yf.Ticker(ticker)
    # print(f"T: {t.info}")
    # holdings = t.info["holdings"]
    # print(f"Holdings: {holdings}")


if __name__ == "__main__":

    ticker = "SPY"
    etf = Etf(ticker)

    h = etf.get_holdings()
    print(f"H: {h}")
