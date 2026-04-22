# Data Sources

This project uses historical price data for all stocks that have ever 
been constituents or reserve stocks of the VN30 index from 2018 to 2024.
Raw data files are not included in this repository.

## Price Data

**Source:** vnstock Python library (KBS source)  
**Coverage:** 63 unique tickers, January 2015 to December 2024  
**Frequency:** Monthly (last trading day of each month)  
**Field used:** Adjusted closing price

To download:
```python
python src/data.py
```

This will download all tickers automatically via vnstock and save to 
`data/processed/prices.csv`. Requires a working internet connection.
Estimated download time: 5-6 minutes (rate limited to 20 requests/minute).

## VN30 Constituent Lists

**Source:** Official HOSE announcements  
**Coverage:** All 14 rebalancing periods from January 2018 to July 2024  
**Verification:** All periods verified against official HOSE PDF documents

VN30 is rebalanced twice yearly — effective the 4th Monday of January 
and July. Constituent lists are hardcoded in `src/data.py` under 
`VN30_CONSTITUENTS` and `VN30_RESERVES`.

## Special Cases

**ROS (FLC Faros Construction):**  
ROS was suspended in March 2022 following the FLC fraud scandal. 
Price data was unavailable via automated sources. Monthly prices were 
manually sourced from cafef.vn using first-of-month prices shifted one 
month to approximate month-end values. This introduces a minor timing 
mismatch for one stock across 2018-2020.

## File Structure

## Disclaimer

Price data is sourced from vnstock which pulls from Vietnamese broker 
APIs (KBS). Data quality has been verified for the VN30 constituent 
periods but may contain gaps or errors for non-constituent periods. 
Users should independently verify data before use in live trading.