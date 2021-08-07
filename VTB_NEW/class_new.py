import requests
import yfinance as yf
import math
import apimoex
import pandas as pd

class Calculations:

    def get_current_price_usd(self):
        security_name = yf.Ticker(self.name)
        data = security_name.history(period='1d')
        if math.isnan(data['Close'][0]):
            price = data['Close'][1]
        else:
            price = data['Close'][0]
        return round(price, 2)

    def get_current_price_rur(self, board, market, ratio):
        with requests.Session() as session:
            data = apimoex.get_board_history(session, self.name, market=market, board=board)
            if not data:
                print(f'no info for {self.name}')
                cur_price = -100
            else:
                dataframe = pd.DataFrame(data)
                cur_price = dataframe.CLOSE.tail(1).array[0]
        # print(cur_price)
        return cur_price * ratio


class Ticker(Calculations):
    def __init__(self, security_df):
        self.raw_name = security_df['Код инструмента'][0]
        self.index_buy_deals = security_df.loc[security_df['B/S'] == 'Покупка'].index.array
        self.index_sell_deals = security_df.loc[security_df['B/S'] == 'Продажа'].index.array
        self.currency = security_df['Валюта'][0]
        self.name = self.stock_name()
        self.length = len(self.name)
        # подсчет количества проданных и купленных бумаг
        self.total_buy = security_df.loc[security_df['B/S'] == 'Покупка', 'Volume'].sum()
        self.total_sell = security_df.loc[security_df['B/S'] == 'Продажа', 'Volume'].sum()
        self.outstanding_volumes = self.total_buy - self.total_sell

    def stock_name(self):
        if self.currency != 'RUR':
            if self.raw_name[-4:] == '_SPB':
                stock_name = self.raw_name[:-4]
        else:
            stock_name = self.raw_name

        return stock_name