import requests
import apimoex
import pandas as pd
import math
import yfinance as yf
from cbrf.models import DynamicCurrenciesRates
import datetime as dt


def get_current_price_rur(ticker, board, market, ratio):
    with requests.Session() as session:
        data = apimoex.get_board_history(session, ticker, market=market, board=board)
        if not data:
            print(f'no info for {ticker}')
            cur_price = -100
        else:
            df = pd.DataFrame(data)
            cur_price = df.CLOSE.tail(1).array[0]
    # print(cur_price)
    return cur_price * ratio


# вычисление котировки на данный момент
def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1d')
    if math.isnan(todays_data['Close'][0]):
        price = todays_data['Close'][1]
    else:
        price = todays_data['Close'][0]
    return price


# функция подстановки ROE в таблицу
def fill_roe(roe_date, currency, date_min):
    def roe_calc(date=roe_date):
        date_max = dt.datetime.now()
        roe_date_mod = pd.to_datetime(date, format="%Y-%m-%d", errors='coerce')

        if currency == "USD":
            id_code = 'R01235'
        else:
            id_code = 'R01239'
        dynamic_rates = DynamicCurrenciesRates(date_min, date_max, id_code)

        return dynamic_rates.get_by_date(roe_date_mod).value

    if currency == "RUR":
        roe = 1
    else:
        try:
            roe = float(roe_calc())
        except AttributeError:
            i = True
            delta = dt.timedelta(days=1)
            roe_date_ = roe_date
            while i:
                roe_date_ = roe_date_ - delta
                try:
                    roe = float(roe_calc(roe_date_))
                    i = False
                except AttributeError:
                    continue
    # print(roe)
    return roe


# НДФЛ
def check_ndfl(profit):
    if profit > 0:
        profit = profit * .85
    return profit


