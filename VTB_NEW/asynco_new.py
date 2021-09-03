import asyncio
import yfinance as yf
import math


async def sec_name(ticker):
    security_name = yf.Ticker(ticker.name)
    if not security_name:
        print(f'no info for {ticker.name}')
        full_name = 'N/A'
        return full_name
    full_name = security_name.info['shortName']
    return full_name


async def usd_eur_price(ticker):
    security_name = yf.Ticker(ticker.name)
    data = security_name.history(period='1d')
    if data.empty:
        print(f'no info for {ticker.name}')
        current_price = -100
        return current_price
    elif math.isnan(data['Close'][0]):
        current_price = data['Close'][1]
    else:
        current_price = data['Close'][0]
        return current_price

async def main(ticker):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete()
    except:
        pass
    full_name = loop.create_task(sec_name(ticker))
    current_price = loop.create_task(usd_eur_price(ticker))
    await asyncio.wait([full_name, current_price])

    return full_name, current_price
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete()
#
# if __name__ == "__main__":
#     try:
#         loop = asyncio.get_event_loop()
#         loop.run_until_complete(main())
#     except:
#         pass

# async def main():
#     taskA = asyncio.create_task(vtb())
#     await taskA
#
# asyncio.run(main())