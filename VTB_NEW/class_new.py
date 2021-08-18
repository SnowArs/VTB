import requests
import yfinance as yf
import math
import apimoex
import pandas as pd
from settings import settings

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
        return cur_price * ratio

    def rub_securities_processing(self, df_):
        if self.length > 4:
            board = 'TQCB'
            market = 'bonds'
            ratio = 10
        else:
            board = 'TQBR'
            market = 'shares'
            ratio = 1

        buy_sum_for_rub_securities =\
            df_.loc[df_.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'RUB_sum'].sum()
        sell_sum_for_rub_securities =\
            df_.loc[df_.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'RUB_sum'].sum()
        average_buy = buy_sum_for_rub_securities / self.total_buy
        average_sell = sell_sum_for_rub_securities / self.total_sell
        current_price = self.get_current_price_rur(board, market, ratio)
        if self.outstanding_volumes == 0:
            prof_loss_for_sold_securities = sell_sum_for_rub_securities - buy_sum_for_rub_securities
            profit_for_outstanding_volumes = 0
        elif math.isnan(average_sell):
            prof_loss_for_sold_securities = 0
            average_sell = 0
            profit_for_outstanding_volumes = (current_price - average_buy) * self.outstanding_volumes
        else:
            prof_loss_for_sold_securities = sell_sum_for_rub_securities - self.total_sell * average_buy
            profit_for_outstanding_volumes = (current_price - average_buy) * self.outstanding_volumes

        total_profit = prof_loss_for_sold_securities + profit_for_outstanding_volumes

        return prof_loss_for_sold_securities, average_buy, profit_for_outstanding_volumes, total_profit


class Ticker(Calculations):
    def __init__(self, security_df, broker):
        self.settings = settings(broker)
        self.raw_name = security_df.iloc[:, self.settings['name']][0]
        self.index_buy_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code']].index.array
        self.buy_volume_array =\
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].array
        self.sale_volume_array =\
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].array
        self.index_sell_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code']].index.array
        self.currency = security_df['Валюта'][0]
        self.broker = broker
        self.name = self.stock_name()
        self.df = security_df
        self.ndfl = 0
        self.profit_in_usd = 0
        self.prof_loss_for_sold_securities_rus = 0
        self.profit_for_outstanding_volumes_rus = 0
        self.total_profit_rus = 0
        # подсчет количества проданных и купленных бумаг
        self.total_buy =\
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].sum()
        self.total_sell =\
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].sum()
        self.buy_sum_for_rub_securities =\
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'RUB_sum'].sum()
        self.sell_sum_for_rub_securities = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'RUB_sum'].sum()
        self.outstanding_volumes = self.total_buy - self.total_sell


    def stock_name(self):
        if self.currency == 'USD':
            if (self.raw_name[-4:] == '_SPB') | (self.raw_name[-3:] == '-RM'):
                stock_name = self.raw_name[:-4]
            else:
                stock_name = self.raw_name
        elif self.currency == 'HKD':
            stock_name = self.raw_name[:-3]
        elif self.currency == 'EUR':
            if self.broker == 'VTB':
                stock_name = self.raw_name[:-4].replace('@', '.')
            elif self.broker == 'IB':
                stock_name = self.raw_name[:-1] + '.DE'
        else:
            stock_name = self.raw_name

        return stock_name
