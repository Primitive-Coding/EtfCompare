from etf import Etf
import numpy as np
import pandas as pd

import datetime as dt
import yfinance as yf

import mplfinance as mpf
import matplotlib.pyplot as plt

import logging

# Suppress logging from Selenium and other related modules
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("peewee").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)


# Set pandas options to display in normal notation
pd.set_option("display.float_format", "{:,.3f}".format)

binance_dark = {
    "base_mpl_style": "dark_background",
    "marketcolors": {
        "candle": {"up": "#3dc985", "down": "#ef4f60"},
        "edge": {"up": "#3dc985", "down": "#ef4f60"},
        "wick": {"up": "#3dc985", "down": "#ef4f60"},
        "ohlc": {"up": "green", "down": "red"},
        "volume": {"up": "#247252", "down": "#82333f"},
        "vcedge": {"up": "green", "down": "red"},
        "vcdopcod": False,
        "alpha": 1,
    },
    "mavcolors": ("#ad7739", "#a63ab2", "#62b8ba"),
    "facecolor": "#1b1f24",
    "gridcolor": "#2c2e31",
    "gridstyle": "--",
    "y_on_right": True,
    "rc": {
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.edgecolor": "#474d56",
        "axes.titlecolor": "red",
        "figure.facecolor": "#161a1e",
        "figure.titlesize": "x-large",
        "figure.titleweight": "semibold",
    },
    "base_mpf_style": "binance-dark",
}


class EtfCompare:
    def __init__(
        self,
        ticker_list: list,
        comparison_start: dt.datetime,
        comparison_end: dt.datetime,
    ) -> None:
        self.start = comparison_start
        self.end = comparison_end
        self.ticker_list = ticker_list
        self.ticker_data = None
        self.ticker_objects = self.create_objects(ticker_list)
        self.color_index = [
            "blue",
            "yellow",
            "cyan",
            "orange",
            "purple",
            "red",
            "grey",
            "grey",
            "grey",
            "grey",
        ]

    def create_objects(self, ticker_list: list):
        object_dict = {}
        self.ticker_data = yf.download(
            tickers=ticker_list, start=self.start, end=self.end, actions=True
        )
        for t in ticker_list:
            etf = Etf(t)
            object_dict[t] = etf
        return object_dict

    """----------------------------------- Compare Operations -----------------------------------"""

    def compare_dividend_growth(self, plot: bool = False):
        dividend_data = {}
        dividends = self.ticker_data["Dividends"]
        cols = dividends.columns.to_list()
        df = pd.DataFrame()
        for c in cols:
            data = dividends[c]
            data = data.loc[data != 0]
            start_div = data.iloc[0]
            end_div = data.iloc[1]
            growth = ((end_div - start_div) / abs(start_div)) * 100
            df.loc["start_date", c] = dt.datetime.strftime(data.index[0], "%Y-%m-%d")

            df.loc["end_date", c] = dt.datetime.strftime(data.index[-1], "%Y-%m-%d")
            df.loc["start", c] = start_div
            df.loc["end", c] = end_div
            df.loc["growth", c] = growth

        return df

    def compare_dividends(self, plot: bool = False):
        dividend_data = {}

        dates = self.ticker_data[list(self.ticker_data.keys())[0]].index

        for k, v in self.ticker_objects.items():
            divs = v.get_dividends(
                self.ticker_data["Close"][k],
                self.ticker_data["Dividends"][k],
                True,
            )
            dividend_data[(k, "dividend")] = divs["dividend"]
            dividend_data[(k, "annual_yield")] = divs["annual_yield"]
            dividend_data[(k, "dividend_growth")] = self._create_trailing_change(
                divs["dividend"]
            )

        data = pd.DataFrame(dividend_data, index=dates)
        if plot:
            data_to_plot = {}
            for t in self.ticker_list:
                data_to_plot[t] = data[t]["dividend"]
            self._create_plot(
                data_to_plot,
                chart_title=f"{self.ticker_list} Dividend Comparison",
                y_axis_label="Dividends ($)",
            )

        else:
            return data

    def _create_plot(
        self, data_to_plot, chart_title: str = "", y_axis_label: str = "Values"
    ):

        # Plotting the data with matplotlib
        plt.figure(figsize=(10, 6))
        color_index = 0
        for k, v in data_to_plot.items():
            index = data_to_plot[k].index
            plt.plot(
                index,
                v,
                label=k,
                color=self.color_index[color_index],
            )

            color_index += 1
        # Adding title and labels
        plt.title(chart_title)
        plt.xlabel("Date")
        plt.ylabel(y_axis_label)

        # Adding a legend
        plt.legend()

        # Display the plot
        plt.show()

    def _create_trailing_change(self, values: pd.Series):
        index = 0
        dates = values.index.to_list()
        data = pd.Series()
        for i in values:
            cur_date = dates[index]
            if index == 0:
                anchor_value = i
                data.loc[cur_date] = np.nan
            else:
                # print(f"[{cur_date}]: {anchor_value}   I: {i}")
                data.loc[cur_date] = ((i - anchor_value) / anchor_value) * 100

            index += 1

        # data.dropna(inplace=True)
        return data


def get_delta(period: int, period_unit: str):
    """
    Create a "timedelta" for date calculations.

    Parameters
    ----------
    period : int
        Number of periods.
    period_unit : str
        The unit of the period. For example, if period=5, and period_unit="Y", then the full period will be 5 years.

    Returns
    -------
    dt.timedelta
        Time delta with the adjusted amount of days according to the 'period_unit'.
    """
    if period_unit == "Y":
        return dt.timedelta(days=(365 * period))
    elif period_unit == "M":
        return dt.timedelta(days=(30 * period))
    elif period_unit == "D":
        return dt.timedelta(days=period)


if __name__ == "__main__":
    ticker_list = ["SPY", "QQQ", "SCHG"]
    end = dt.datetime.now()
    start = end - get_delta(5, "Y")
    etf = EtfCompare(ticker_list, start, end)
    df = etf.compare_dividends(False)

    print(df["SCHG"])

    print(etf.compare_dividend_growth())
    # df = etf.compare_dividend_growth(plot=True)
    # print(f"DF: {df}")
