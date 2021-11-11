import xml.etree.ElementTree as ET
import httplib2


def current_prices(full_list_of_securities_rub):
    MAIN_URL = 'https://iss.moex.com/iss/engines/stock/markets'
    MOEX_FINANCE_URL_SEC = MAIN_URL + '/shares/boards/TQBR/securities.xml?iss.meta=off&iss.only=s' \
                                      'ecurities&securities.columns=SECID,SECNAME,PREVADMITTEDQUOTE'
    MOEX_FINANCE_URL_BONDS = MAIN_URL + '/bonds/boards/TQCB/securities.xml?iss.meta=off&iss.only=' \
                                        'securities&securities.columns=SECID,SECNAME,PREVADMITTEDQUOTE'
    MOEX_FINANCE_URL_ETF = MAIN_URL + '/shares/boards/TQTF/securities.xml?iss.meta=off&iss.only=' \
                                      'securities&securities.columns=SECID,SECNAME,PREVADMITTEDQUOTE'

    urls = [MOEX_FINANCE_URL_SEC, MOEX_FINANCE_URL_BONDS, MOEX_FINANCE_URL_ETF]
    prices_rur_arr = []

    for url in urls:
        h = httplib2.Http(".cache")
        (resp_headers, content) = h.request(url, "GET")
        root = ET.fromstring(content)
        for data in root:
            for rows in data:
                for row in rows:
                    ticker = row.get('SECID')
                    name = row.get('SECNAME')
                    price = row.get('PREVADMITTEDQUOTE')
                    if ticker in full_list_of_securities_rub:
                        prices_rur_arr.append([ticker, name, price])
                        full_list_of_securities_rub.remove(ticker)
    for no_data_ticker in full_list_of_securities_rub:
        prices_rur_arr.append([no_data_ticker, '', 0])

    return prices_rur_arr


if __name__ == "__main__":
    current_prices()
