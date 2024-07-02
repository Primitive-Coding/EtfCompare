# ETF Compare

- Scrape ETF holdings and save them locally.
- Compare dividends and their growth rate.

- **Other Features**
  - Historical Dividend Yields
  - Dynamically creating graphs with indicators.

---

### Setup

1. Clone git repository: `https://github.com/Primitive-Coding/EtfCompare.git`

2. Install the projects requirements with `pip install -r requirements.txt`

---

### Instructions

- Create a class instance.

```
    ticker_list = ["SPY", "QQQ", "SCHG"]
    end = dt.datetime.now()
    start = end - get_delta(5, "Y")
    etf_compare = EtfCompare(ticker_list, start, end)
```

###### Compare Dividend Growth Rates

```
    etf_compare.compare_dividend_growth()

    # Output
                    QQQ        SCHG         SPY
    start_date  2019-09-23  2019-09-25  2019-09-20
    end_date    2024-06-24  2024-06-26  2024-06-21
    start            0.384       0.104       1.384
    end              0.458       0.098       1.570
    growth          19.271      -6.220      13.439
```

---

# ETF

- If you only want ETF data, you can use the custom `ETF` class.
- Below is how to create an instance.

```
    etf = Etf("SPY")
```

##### Get Holdings

```
    etf = Etf("SPY")
    etf.get_holdings()

    # Output
                                 name weight  shares_held   market_value
    symbol
    MSFT                      Microsoft Corp  7.29%  87600000.00 39600000000.00
    NVDA                         NVIDIA Corp  6.74% 289800000.00 39600000000.00
    AAPL                           Apple Inc  6.67% 169800000.00 39600000000.00
    AMZN                      Amazon.com Inc  3.85% 107900000.00 39600000000.00
    META          Meta Platforms Inc Class A  2.44%  25800000.00 39600000000.00
    ...                                  ...    ...          ...            ...
    BIO     Bio-Rad Laboratories Inc Class A  0.01%    246200.00    84100000.00
    PARA            Paramount Global Class B  0.01%   5700000.00    84100000.00
    NWS                    News Corp Class B  0.01%   1400000.00    84100000.00
    PAYC                 Paycom Software Inc  0.01%    574500.00    84100000.00
    MHK                Mohawk Industries Inc  0.01%    605200.00    84100000.00
```
