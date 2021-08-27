import requests
import yfinance as yf
import math
import apimoex
import pandas as pd
from tradingview_ta import TA_Handler, Interval, Exchange
from settings import settings


class Calculations:

    def get_current_price(self, board='', market='', ratio=1):
        def hkd():
            security_data = TA_Handler(
                symbol=self.name,
                screener="hongkong",
                exchange="HKEX",
                interval=Interval.INTERVAL_1_DAY
            )
            print(self.name, security_data.get_analysis().indicators['close'])
            self.current_price = security_data.get_analysis().indicators['close']
            return self

        def rur():
            with requests.Session() as session:
                data = apimoex.get_board_history(session, self.name, market=market, board=board)
                if not data:
                    print(f'no info for {self.name}')
                    current_price = -100
                else:
                    dataframe = pd.DataFrame(data)
                    current_price = dataframe.CLOSE.tail(1).array[0]
            self.current_price = current_price * ratio
            return self

        def usd_eur_exchange():
            security_name = yf.Ticker(self.name)
            data = security_name.history(period='1d')
            if data.empty:
                print(f'no info for {self.name}')
                self.current_price = -100
            elif math.isnan(data['Close'][0]):
                self.current_price = data['Close'][1]
            else:
                self.current_price = data['Close'][0]
            return self

        if self.currency == 'HKD':
            self = hkd()
        elif self.currency == 'RUR':
            self = rur()
        else:
            self = usd_eur_exchange()
        return self.current_price


    def rub_securities_processing(self, df_):
        if self.length > 4:
            board = 'TQCB'
            market = 'bonds'
            ratio = 10
        else:
            board = 'TQBR'
            market = 'shares'
            ratio = 1

        buy_sum_for_rub_securities = \
            df_.loc[df_.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'RUB_sum'].sum()
        sell_sum_for_rub_securities = \
            df_.loc[df_.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'RUB_sum'].sum()
        average_buy = buy_sum_for_rub_securities / self.total_buy
        average_sell = sell_sum_for_rub_securities / self.total_sell
        current_price = self.get_current_price_rur(board, market, ratio)
        if self.outstanding_volumes == 0:
            prof_for_sold_securities = sell_sum_for_rub_securities - buy_sum_for_rub_securities
            profit_for_outstanding_volumes = 0
        elif math.isnan(average_sell):
            prof_for_sold_securities = 0
            average_sell = 0
            profit_for_outstanding_volumes = (current_price - average_buy) * self.outstanding_volumes
        else:
            prof_for_sold_securities = sell_sum_for_rub_securities - self.total_sell * average_buy
            profit_for_outstanding_volumes = (current_price - average_buy) * self.outstanding_volumes

        full_profit = prof_for_sold_securities + profit_for_outstanding_volumes

        return prof_for_sold_securities, average_buy, profit_for_outstanding_volumes, full_profit


class Ticker(Calculations):
    def __init__(self, security_df, broker):
        self.settings = settings(broker)
        self.raw_name = security_df.iloc[:, self.settings['name']][0]
        self.index_buy_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code']].index.array
        self.buy_volume_array = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].array
        self.sale_volume_array = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].array
        self.index_sell_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code']].index.array
        self.currency = security_df['Валюта'][0]
        self.broker = broker
        self.board = ''
        self.market = ''
        self.ratio = 1
        self.name = self.stock_name()
        self.df = security_df
        self.current_price = round(self.get_current_price(self.board, self.market, self.ratio), 2)
        self.exchange_to_usd = self.exchange()
        self.average_roe_for_outstanding_volumes = 0

        self.ndfl = 0
        self.ndfl_full = 0
        self.full_profit = 0
        self.prof_for_sold_securities = 0
        self.profit_for_outstanding_volumes = 0
        # подсчет количества проданных и купленных бумаг
        self.total_buy = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].sum()
        self.total_sell = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].sum()
        self.buy_sum_for_rub_securities = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'RUB_sum'].sum()
        self.sell_sum_for_rub_securities = \
            security_df.loc[
                security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'RUB_sum'].sum()
        self.outstanding_volumes = self.total_buy - self.total_sell

    def stock_name(self):
        if self.currency == 'USD':
            if (self.raw_name[-4:] == '_SPB') | (self.raw_name[-3:] == '-RM'):
                stock_name = self.raw_name[:-4]
            else:
                stock_name = self.raw_name
        elif self.currency == 'HKD':
            stock_name = self.raw_name
            self.ratio = 10
        elif self.currency == 'EUR':
            if self.broker == 'VTB':
                stock_name = self.raw_name[:-4].replace('@', '.')
            elif self.broker == 'IB':
                stock_name = self.raw_name[:-1] + '.DE'
        elif self.currency == 'RUR':
            stock_name = self.raw_name
            if len(stock_name) > 4:
                self.board = 'TQCB'
                self.market = 'bonds'
                self.ratio = 10
            else:
                self.board = 'TQBR'
                self.market = 'shares'
                self.ratio = 1

        return stock_name

    def exchange(self):
        if self.currency == 'USD':
            exc = 1
            return exc
        if self.currency == 'RUR':
            symbol = f'RUBUSD=X'
        else:
            symbol = f'{self.currency}USD=X'
        security_name = yf.Ticker(symbol)
        data = security_name.history(period='1d')
        if data.empty:
            print(f'no info for {symbol}')
            exc = -100
        elif math.isnan(data['Close'][0]):
            exc = data['Close'][1]
        else:
            exc = data['Close'][0]
        return exc
