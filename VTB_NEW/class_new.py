import requests
import yfinance as yf
import math
import apimoex
import pandas as pd
from tradingview_ta import TA_Handler, Interval, Exchange
import BD
import numpy as np
import asynco_new
import sec_prices_rub

# from modules import excel_saving


# class Calculations:

    # # def get_current_price(self, board='', market=''):
    #

    #
    #     def rur_security_name_and_prices(name_y_n):
    #         with requests.Session() as session:
    #             data = apimoex.get_board_history(session, self.name, market=self.market, board=self.board)
    #             if not data:
    #                 print(f'no info for {self.name}')
    #                 self.current_price = 'N/A'
    #                 return self
    #             else:
    #                 dataframe = pd.DataFrame(data)
    #                 current_price = dataframe.CLOSE.tail(1).array[0]
    #                 if math.isnan(current_price):
    #                     self.current_price = 'closed'
    #         self.current_price = round(current_price * self.bonds_mult, 2)
    #
    #         if data:
    #             if name_y_n != 'Y':
    #                 data1 = apimoex.find_security_description(session, self.ticker)
    #                 self.full_name = data1[2]['value']
    #
    #     return self
    #
    # # def usd_eur_gbp_security_name_and_prices(self, name_y_n):
    #     security_name = yf.Ticker(self.ticker)
    #     try:
    #         data = security_name.history(period='1d')
    #         if data.empty:
    #             print(f'no info for {self.ticker}')
    #             self.current_price = 'N/A'
    #             # return self
    #         elif math.isnan(data['Close'][0]):
    #             self.current_price = round(data['Close'][1], 2) * self.bonds_mult
    #         else:
    #             self.current_price = round(data['Close'][0], 2) * self.bonds_mult
    #         if (name_y_n != 'Y') & (not data.empty):
    #             self.full_name = security_name.info['shortName']
    #             BD.update_bd_with_names(self)
    #         elif (name_y_n != 'Y') & (self.full_name != ''):
    #             BD.update_bd_with_names(self)
    #
    #     except:
    #         print('JSONDecodeError')
    #         return self
    #
    #
    #
    #     # загрузка базы с именами, чтобы ускорить процесс
    #     base_with_company_names = BD.load_names()
    #     name_y_n = 'N'
    #     if self.outstanding_volumes == 0:
    #         self.current_price = 0
    #         return self.current_price
    #
    #     elif self.ticker in base_with_company_names['Тикер'].astype('str').array:
    #         self.full_name = base_with_company_names.loc[base_with_company_names['Тикер'] == self.ticker,
    #                                                      'Название компании'].array[0]
    #         name_y_n = 'Y'


        # return self.current_price


class Ticker:
    def __init__(self, security_df, df_with_currencies_exchange, path_to, df_for_execution):
        self.df = security_df
        self.df_for_execution = df_for_execution
        self.ticker = security_df['ticker'][0]
        self.currency = security_df['currency'][0]
        self.broker = security_df['broker'][0]
        self.full_name = security_df['name'][0]
        self.type = security_df['sec_type'][0]
        self.volume_mult = 1 # коэффициент объемов, обычно в облигациях или опционах
        self.bonds_mult = 1 # коэффициент бондов, используется в цене
        self.ratio = 1 #коэф для бумаг, где программа выдает цену за несколько штук
        self.board = ''
        self.market = ''
        self.path_to = path_to
        self.corrected_name_to_get_price = self.security_name()
        self.current_price = self.price_level_2() # расчет цены с апдейтированным тикером
        self.commission = self.commission()
        self.average_price_usd = 'N/A'
        self.index_sell_deals = security_df.loc[security_df['buy_sell'] == 'Продажа'].index.array
        self.index_buy_deals = security_df.loc[security_df['buy_sell'] == 'Покупка'].index.array
        self.buy_volume_array = np.array(
            security_df.loc[security_df['buy_sell'] == 'Покупка', 'volume'].array) * self.volume_mult
        self.sale_volume_array = np.array(
            security_df.loc[security_df['buy_sell'] == 'Продажа', 'volume'].array) * self.volume_mult
        self.exchange_to_usd = self.exchange(df_with_currencies_exchange)
        self.average_roe_for_outstanding_volumes = 0
        self.filled_row = 0
        self.full_profit = 0
        self.prof_for_sold_securities_rub = 0
        self.prof_for_sold_securities = 0
        self.profit_for_outstanding_volumes = 0
        # подсчет количества проданных и купленных бумаг
        self.total_buy = security_df.loc[security_df['buy_sell'] == 'Покупка', 'volume'].sum() * self.volume_mult
        self.total_sell = security_df.loc[security_df['buy_sell'] == 'Продажа', 'volume'].sum() * self.volume_mult
        self.buy_sum_for_rub_securities = security_df.loc[security_df['buy_sell'] == 'Покупка', 'RUB_sum'].sum()
        self.sell_sum_for_rub_securities = security_df.loc[security_df['buy_sell'] == 'Продажа', 'RUB_sum'].sum()
        self.outstanding_volumes = self.total_buy - self.total_sell

    #проход по новому имени , если оно есть
    def price_level_2(self):

        if self.corrected_name_to_get_price != '':   #) & (self.currency == 'HKD') :

            ticker, name, price = asynco_new.main([self.corrected_name_to_get_price])[0]
            if price:
                print(self.corrected_name_to_get_price)
                self.df_for_execution.loc[self.df_for_execution['ticker'] == self.ticker, ['cur_price', 'name']] = price, name
                self.current_price = price * self.ratio
                self.full_name = name
            elif self.currency == 'HKD':
                price = sec_prices_rub.hkd_security_name_and_prices(self.ticker)
                if price:
                    self.df_for_execution.loc[
                        self.df_for_execution['ticker'] == self.ticker, ['cur_price', 'name']] = price, 'no data'
                    self.current_price = price * self.ratio
                    self.full_name = 'no data'
        else:
            self.current_price = self.df['cur_price'][0] * self.bonds_mult
        try:
            if not self.current_price:
                pass
        except AttributeError:
            self.current_price = 0

        return self.current_price

    # def sale_volume_array(self):
    #     sale_arr = np.array(self.df.loc[self.df['buy_sell'] == 'Продажа', 'volume'].array) * self.volume_mult
    #     if not sale_arr:
    #         sale_arr = []
    #     return sale_arr

    def security_name(self):
        print(self.ticker)
        #загрузка алтернативной базы имен
        df_alternative_names = pd.read_excel(self.path_to + r'\alternative_names.xlsx')
        # работа с базой альтернативных имен для получения цен и названий

        if self.ticker in df_alternative_names.name.array:
            self.corrected_name_to_get_price = \
                df_alternative_names.loc[df_alternative_names.name == self.ticker].alter_name.values[0]
            self.ratio = \
                df_alternative_names.loc[df_alternative_names.name == self.ticker].mult.values[0]
        else:
            self.corrected_name_to_get_price = ''

        stock_name = self.ticker
        if self.currency == 'USD':
            if self.broker == 'IB':
                if len(self.ticker) > 10:  # определение облигаций и опционов
                    options = ('_C', '_P')
                    if self.ticker.endswith(options):
                        self.volume_mult = 100
                        self.type = 'Опцион'
                    else:
                        self.volume_mult = 0.001
                        self.bonds_mult = 10
                        self.type = 'Еврооблигация'
                # обработка привелигерованных акций
                elif (self.ticker.endswith(' PR', 4, 7)) | (self.ticker.endswith(' PR', 3, 6)):
                    self.corrected_name_to_get_price = self.ticker.replace(' PR', '-P')
                    self.type = 'Иностранные акции'
            elif self.broker == 'SBER':
                if len(self.ticker) > 10:
                    self.bonds_mult = 10
                    self.type = 'Еврооблигация'

        elif self.currency == 'GBP':
            self.type = 'Иностранные акции в фунтах'
            self.corrected_name_to_get_price = self.ticker + '.L'
        elif self.currency == 'HKD':
            self.corrected_name_to_get_price = self.ticker + '.HK'
            self.type = 'Китайские акции'
            # self.ratio = 10

        elif self.currency == 'EUR':
            if len(stock_name) > 7:
                self.type = 'Иностранные облигации в евро'
                self.bonds_mult = 10
            else:
                self.type = 'Иностранные акции в евро'
                if self.broker == 'VTB':
                    self.corrected_name_to_get_price = self.ticker.replace('@', '.')
                elif self.broker == 'IB':
                    self.corrected_name_to_get_price = self.ticker[:-1] + '.DE'

        elif (self.currency == 'RUR') | (self.currency == 'RUB'):
            if len(stock_name) > 5:
                self.board = 'TQCB'
                self.market = 'bonds'
                if self.broker != 'VTB':
                    self.bonds_mult = 10
                self.type = 'Российские облигации'

            else:
                self.board = 'TQBR'
                self.market = 'shares'
                self.type = 'Российские акции'

        return self.corrected_name_to_get_price

    def exchange(self, df_cur):
        if self.currency == 'USD':
            exchange = 1
        elif self.currency == 'RUR':
            self.currency = 'RUB'
            exchange = df_cur.loc[df_cur.name.str.contains(self.currency)].ROE.values[0]
        else:
            exchange = df_cur.loc[df_cur.name.str.contains(self.currency)].ROE.values[0]
        return exchange

    def commission(self):
        if self.broker == 'VTB':
            commission = 0.001
        elif self.broker == 'FRIDOM':
            commission = self.df['commission'].sum()
        elif self.broker == 'IB':
            commission = 0.001
        if self.broker == 'SBER':
            commission = self.df['commission'].sum()
        return commission

