import requests
import yfinance as yf
import math
import apimoex
import pandas as pd
from tradingview_ta import TA_Handler, Interval, Exchange
from settings import settings
import BD
import numpy as np
import asynco_new


class Calculations:

    def get_current_price(self, board='', market='', ratio=1):
        def hkd(name_y_n):
            security_data = TA_Handler(
                symbol=self.name,
                screener="hongkong",
                exchange="HKEX",
                interval=Interval.INTERVAL_1_DAY
            )
            # print(self.name, security_data.get_analysis().indicators['close'])
            self.current_price = security_data.get_analysis().indicators['close']
            if name_y_n != 'Y':
                pass
            return self

        def rur(name_y_n):
            with requests.Session() as session:
                data = apimoex.get_board_history(session, self.name, market=market, board=board)
                if not data:
                    print(f'no info for {self.name}')
                    current_price = -100
                    return self
                else:
                    dataframe = pd.DataFrame(data)
                    current_price = dataframe.CLOSE.tail(1).array[0]
            self.current_price = current_price * ratio

            if name_y_n != 'Y':
                data1 = apimoex.find_security_description(session, self.name)
                self.full_name = data1[2]['value']
            return self

        def usd_eur_exchange(name_y_n):
            #     name = asynco_new.main(self.name)
            #     print(name)
            security_name = yf.Ticker(self.name)
            data = security_name.history(period='1d')
            if data.empty:
                print(f'no info for {self.name}')
                self.current_price = -100
                self.full_name = 'N/A'
                return self
            elif math.isnan(data['Close'][0]):
                self.current_price = data['Close'][1]
            else:
                self.current_price = data['Close'][0]
            if name_y_n != 'Y':
                self.full_name = security_name.info['shortName']
            return self

        # загрузка базы с именами
        base_with_company_names = BD.load_names()
        name_y_n = 'N'
        if self.outstanding_volumes == 0:
            self.current_price = 0
            return self.current_price

        elif self.name in base_with_company_names['Тикер'].astype('str').array:
            self.full_name = base_with_company_names.loc[base_with_company_names['Тикер'] == self.name,
                                                         'Название компании'].array[0]
            name_y_n = 'Y'

        if self.currency == 'HKD':
            self = hkd(name_y_n)
        elif self.currency == 'RUR':
            self = rur(name_y_n)
        else:
            self = usd_eur_exchange(name_y_n)
        return self.current_price


class Ticker(Calculations):
    def __init__(self, security_df, broker):
        self.settings = settings(broker)
        self.df = security_df
        self.raw_name = security_df.iloc[:, self.settings['name']][0]

        # self.buy_volume_array = \
        #     security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].array
        # self.sale_volume_array = \
        #     security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].array
        self.index_sell_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code']].index.array
        self.currency = security_df['Валюта'][0]
        self.broker = broker
        self.volume_mult = 1
        self.bonds_mult = 1
        self.full_name = ''
        self.type = ''
        self.board = ''
        self.market = ''
        self.ratio = 1
        self.name = self.stock_name()
        self.index_buy_deals = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code']].index.array
        self.buy_volume_array = np.array(
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].array) \
                                * self.volume_mult
        self.sale_volume_array = np.array(
            security_df.loc[
                security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].array) \
                                 * self.volume_mult

        self.exchange_to_usd = self.exchange()
        self.average_roe_for_outstanding_volumes = 0

        self.filled_row = 0
        self.ndfl = 0
        self.ndfl_full = 0
        self.full_profit = 0
        self.prof_for_sold_securities = 0
        self.profit_for_outstanding_volumes = 0
        # подсчет количества проданных и купленных бумаг
        self.total_buy = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'Volume'].sum()\
            * self.volume_mult
        self.total_sell = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'Volume'].sum() \
            * self.volume_mult
        self.buy_sum_for_rub_securities = \
            security_df.loc[security_df.iloc[:, self.settings['buy_col']] == self.settings['buy_code'], 'RUB_sum'].sum()
        self.sell_sum_for_rub_securities = \
            security_df.loc[
                security_df.iloc[:, self.settings['buy_col']] == self.settings['sell_code'], 'RUB_sum'].sum()
        self.outstanding_volumes = self.total_buy - self.total_sell
        self.current_price = round(self.get_current_price(self.board, self.market, self.ratio), 2) * self.bonds_mult

    def stock_name(self):
        if self.currency == 'USD':
            self.type = 'Иностранные акции'
            if self.broker == 'IB':
                if len(self.raw_name) > 10:
                    options = ('_C', '_P')
                    if self.raw_name.endswith(options):
                        self.volume_mult = 100
                        self.type = 'Опцион'
                    else:
                        self.volume_mult = 0.001
                        self.bonds_mult = 10
                        self.type = 'Облигация'
                    stock_name = self.raw_name
                elif (self.raw_name.endswith(' PR', 4, 7)) | (self.raw_name.endswith(' PR', 3, 6)):
                    stock_name = self.raw_name.replace(' PR', '-P')
                else:
                    stock_name = self.raw_name
            else:
                stock_name = self.raw_name
        elif self.currency == 'GBP':
            self.bonds_mult = 0.010 # Пока только для FRES
            self.type = 'Иностранные акции в фунтах'
            stock_name = self.raw_name + '.L'
        elif self.currency == 'HKD':
            stock_name = self.raw_name
            self.type = 'Китайские акции'
            self.ratio = 10
        elif self.currency == 'EUR':
            self.type = 'Иностранные акции в евро'
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
                self.type = 'Российские облигации'
            else:
                self.board = 'TQBR'
                self.market = 'shares'
                self.ratio = 1
                self.type = 'Российские акции'

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
