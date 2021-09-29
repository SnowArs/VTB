import argparse
import asyncio
import itertools
import pprint
from decimal import Decimal
from typing import List, Tuple
import httpx
import yfinance as yf
import math

YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
YAHOO_FINANCE_URL_ADV = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}?modules=price'

async def fetch_price(
    ticker: str, client: httpx.AsyncClient
) -> Tuple[str, Decimal]:
    print(f"Making request for {ticker} price")
    response = await client.get(YAHOO_FINANCE_URL_ADV.format(ticker))
    print(f"Received results for {ticker}")
    price = response.json()["quoteSummary"]["result"][0]["price"]["regularMarketPrice"]['raw']
    name = response.json()["quoteSummary"]["result"][0]["price"]["shortName"]
    return ticker, name, price #Decimal(price).quantize(Decimal("0.01"))


async def get_current_price_usd(symbol, client: httpx.AsyncClient):
    ticker = await client.get(yf.Ticker(symbol))
    todays_data = ticker.history(period='1d')
    if len(todays_data) == 0:
        price = float('nan')
    else:
        if math.isnan(todays_data['Close'][0]):
            price = todays_data['Close'][1]
        else:
            price = round(todays_data['Close'][0], 2)
    return symbol, price


async def fetch_all_prices(tickers: List[str]) -> List[Tuple[str, Decimal]]:
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *map(fetch_price, tickers, itertools.repeat(client),)
        )
if __name__ == "__main__":

    tickers = ['VTSAX', 'VTIAX', 'IJS', 'VSS', 'AAPL', 'ORCL', 'GOOG', 'MSFT', 'FB']

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(fetch_all_prices(tickers))
    pprint.pprint(result)
    input()