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

# for name in array_with_results:
#     name_arr.append([name[0], name[13]])
# print(name_arr)
# [['FRHC', ''], ['HOLX', 'Hologic, Inc.'], ['TEF', ''], ['CACI', ''], ['CPNG', ''], ['FEYE', 'FireEye, Inc.'], ['CRUS', ''], ['IIVI', ''], ['OLO', ''], ['ACVA', 'ACV Auctions Inc.'], ['DOCN', ''], ['VZIO', ''], ['DSGN', 'Design Therapeutics, Inc.'], ['ACHL', ''], ['COUR', ''], ['ALKT', 'Alkami Technology, Inc.'], ['APP', 'Applovin Corporation'], ['TSP', ''], ['AKYA', 'Akoya BioSciences, Inc.'], ['RXRX', ''], ['DV', ''], ['PATH', 'UiPath, Inc.'], ['ZY', 'Zymergen Inc.'], ['RAIN', 'Rain Therapeutics Inc.'], ['VACC', 'Vaccitech plc'], ['TALS', 'Talaris Therapeutics, Inc.'], ['GLBE', ''], ['SMWB', 'Similarweb Ltd.'], ['PAY', 'Paymentus Holdings, Inc.'], ['MQ', 'Marqeta, Inc.'], ['MNDY', 'monday.com Ltd.'], ['WKME', 'WalkMe Ltd.'], ['VERV', 'Verve Therapeutics, Inc.'], ['CYT', 'Cyteir Therapeutics, Inc.'], ['CFLT', 'Confluent, Inc.'], ['DOCS', 'Doximity, Inc.'], ['RPID', 'Rapid Micro Biosystems, Inc.'], ['SGHT', 'Sight Sciences, Inc.'], ['BLND', 'Blend Labs, Inc.'], ['BASE', 'Couchbase, Inc.'], ['CTKB', 'Cytek Biosciences, Inc.'], ['DUOL', 'Duolingo, Inc.'], ['WLL', 'Whiting Petroleum Corporation'], ['KTOS', 'Kratos Defense & Security Solut'], ['MU', 'Micron Technology, Inc.'], ['FDX', 'FedEx Corporation']]
# df_to_save = pd.DataFrame(name_arr, columns=['Тикер', 'Название компании'])
# df_to_save = df_to_save.loc[df_to_save['Название компании'] !='']
# df_to_save.to_excel('Company_names.xls')