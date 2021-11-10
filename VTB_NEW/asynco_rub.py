import argparse
import asyncio
import itertools
import pprint
from decimal import Decimal
from typing import List, Tuple
import httpx
from xml.etree import ElementTree

YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
YAHOO_FINANCE_URL_ADV = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.xml?iss.meta=off&iss.only=securities&securities.columns=SECID,PREVADMITTEDQUOTE'


async def fetch_price(
        ticker: str, client: httpx.AsyncClient
) -> Tuple[str, Decimal]:
    print(f"Making request for {ticker} price")
    response = await client.get(YAHOO_FINANCE_URL_ADV)
    response1 = await client.get(YAHOO_FINANCE_URL_ADV)
    xml_root = ElementTree.fromstring(response.content)
    root = response1.getroot()
    print(f"Received results for {ticker}")
    try:
        price = response.xml()["quoteSummary"]["result"][0]["price"]["regularMarketPrice"]['raw']
        name = response.json()["quoteSummary"]["result"][0]["price"]["shortName"]
    except:
        price = 0

    return ticker, price  # Decimal(price).quantize(Decimal("0.01"))


async def fetch_all_prices(tickers: List[str]) -> List[Tuple[str, Decimal]]:
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *map(fetch_price, tickers, itertools.repeat(client), )
        )


def main():
    tickers = ['RU000A0JUV81']

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(fetch_all_prices(tickers))
    # pprint.pprint(result)
    return result
    # input()


if __name__ == "__main__":
    main()