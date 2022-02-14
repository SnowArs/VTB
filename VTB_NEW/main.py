import warnings
from VTB_NEW.modules import excel_saving
from moex import *
import class_new
from func import culc, outstanding_volume_price
import asynco_new
import sec_prices_rub
from prettytable import PrettyTable
import settings_for_sec

warnings.filterwarnings('ignore')

CURRENCIES = ['RUBUSD=X', 'EURUSD=X', 'GBPUSD=X', 'HKDUSD=X']


def append_to_total_profit(ticker, total_combined_profit):
    if ticker.full_profit != 'N/A':
        total_combined_profit += ticker.prof_for_sold_securities
    return total_combined_profit


#печать таблицы
def output(table, tot_combined_profit, prof_per_year_dct, prof_rub_per_year_dct):
    print()
    print(table)
    print(f'общая прибыль по всем бумагам в USD до уплаты налогов: {int(tot_combined_profit)}')
    print('-' * 20)
    print(f'year 2020 - profit от закрытых сделок:  {round(sum(prof_per_year_dct["2020"]), 0)}, USD, '
          f'year 2020 - НДФЛ по закрытым сделкам: {round(sum(prof_rub_per_year_dct["2020"]) * 0.15, 0)}, RUR ')
    print('-' * 20)
    print(f'year 2021 - profit от закрытых сделок: {round(sum(prof_per_year_dct["2021"]), 0)}, USD, '
          f'year 2021 - НДФЛ по закрытым сделкам: {round(sum(prof_rub_per_year_dct["2021"]) * 0.15, )}, RUR ')
    print('-' * 20)
    print(f'year 2022 - profit от закрытых сделок: {round(sum(prof_per_year_dct["2022"]), 0)}, USD, '
          f'year 2022 - НДФЛ по закрытым сделкам: {round(sum(prof_rub_per_year_dct["2022"]) * 0.15, 0)}, RUR ')
    return None

def old_new_tickers_comb(old_ticker, df_new, df_full):
    # создание таблицы нового и старого названия
    old_ticker_df = df_full.loc[df_full.ticker == old_ticker]
    df_new = df_new.append(old_ticker_df, ignore_index=True).sort_values(by=['date'])
    return df_new


""""" 
1/ создаются таблицы для вывода в более читаемом выводе, чем вывод датафрейма
2/ 
"""""


def main_func(df, path, exception_arr=[]):
    df_for_execution = df.loc[~df.ticker.isin(exception_arr)].reset_index(drop=True)
    # загрузка алтернативной базы имен
    df_alternative_names = pd.read_excel(path + r'\alternative_names.xlsx')

    # выделяем отдельно рублевые бумаги для получения цены через сайт МБ
    full_list_of_securities_rub = set(df_for_execution.loc[df_for_execution.currency.str.contains('RUB|RUR')].ticker)
    df_sec_prices_rub = pd.DataFrame(sec_prices_rub.current_prices(list(full_list_of_securities_rub)),
                                     columns=['ticker', 'name', 'cur_price'])
    # выделяем отдельно валютные бумаги для получения цены через сайт yahoo (отдельная история с GBP и HKD)
    full_list_of_securities_non_rub = set(df_for_execution.loc[~df_for_execution.currency.str.contains('RUB|RUR')].
                                          ticker)
    list_with_names_and_prices_non_rub = asynco_new.main(full_list_of_securities_non_rub)
    df_sec_prices_non_rub = pd.DataFrame(list_with_names_and_prices_non_rub, columns=['ticker', 'name', 'cur_price'])
    # отдельно DF по валюте
    currencies_exchange = asynco_new.main(CURRENCIES)
    df_with_currencies_exchange = pd.DataFrame(currencies_exchange, columns=['currency', 'name', 'ROE'])
    # могут быть повторяющиеся тикеры, поэтому надо сложить
    full_list_of_securities = list(full_list_of_securities_rub) + list(full_list_of_securities_non_rub)
    df_full = df_sec_prices_rub.append(df_sec_prices_non_rub)
    df_for_execution = df_for_execution.merge(df_full, how='outer', on='ticker', sort=True)
    df_for_execution = df_for_execution.astype({'cur_price': 'float'})

    # сознадние таблицы вывода
    mytable = PrettyTable()
    # имена полей таблицы
    mytable.field_names = settings_for_sec.pretty_table_fields()

    total_combined_profit = 0
    error_arr = []
    array_with_results = []
    prof_per_year_dict = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    prof_rub_per_year_dict = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}

    """"" 
    2/ по каждой бумаге в портфеле производится подсчет показателей прибыльности
    """""
    # for security in ['CLNY-PJ']:
    for security in sorted(full_list_of_securities):
        # print(f'processing {security}')
    # проверка на смену тикера
        try:
            is_old_ticker = df_alternative_names.loc[df_alternative_names.name == security].type[0]
        except KeyError:
            is_old_ticker = ''
        if is_old_ticker == 'old':
            continue

        df_for_security = df_for_execution.loc[df_for_execution.ticker == security].reset_index(drop=True)
        #создаем расширеный датафрейм если тикер поменялся
        if security in df_alternative_names.alter_name.array:
            old_ticker = df_alternative_names.loc[df_alternative_names.alter_name == security].name.array[0]
            df_for_security = old_new_tickers_comb(old_ticker, df_for_security, df_for_execution)


        if df_for_security.empty:  # проверка на пустую таблицу по инструменту
            print(f'пустая датафрейм для  {security}')
            error_arr.append(security)
            continue
        else:
            ticker = class_new.Ticker(df_for_security, df_with_currencies_exchange, path, df_for_execution)
            df_for_execution = ticker.df_for_execution
            ticker.df = pd.concat([ticker.df, pd.DataFrame(columns=['profit_rus', 'prof_usd'])])

            # указание на ошибку если остаток акций отрицательный, скорее всего из-за сплита
            if (ticker.outstanding_volumes < 0) or (ticker.index_buy_deals.size == 0):
                print(f'похоже в позиции {ticker.ticker} проблемы с вычислениями, так как остаток отрицательный')
                error_arr.append(security)
                continue
            # ошибка пропущенных покупок, либо шорт
            elif (ticker.index_sell_deals.size > 0) and (ticker.index_buy_deals.size > 0):
                if ticker.index_sell_deals[0] < ticker.index_buy_deals[0]:
                    input(f'похоже в позиции {ticker.ticker} пропущены покупки, так как таблица начинается с продаж')
                    error_arr.append(security)
                    continue
            elif ticker.sale_volume_array.size != 0:
                start = True
                i = 1
                while start:
                    if ticker.sale_volume_array[-i] < abs(ticker.outstanding_volumes):
                        ticker.sale_volume_array[-i - 1] += ticker.sale_volume_array[-i]
                        ticker.df.iat[ticker.index_sell_deals[-1 - 1], 5] += ticker.df.iat[
                            ticker.index_sell_deals[-1], 5]
                        ticker.sale_volume_array = ticker.sale_volume_array[:-1]
                        ticker.df.drop(ticker.index_sell_deals[-1], inplace=True)
                        ticker.index_sell_deals = ticker.index_sell_deals[:-1]
                        i += 1
                        continue
                    else:
                        ticker.sale_volume_array[-1] = int(ticker.sale_volume_array[-1] + ticker.outstanding_volumes)

                        ticker.df.iat[ticker.index_sell_deals[-1], 5] = \
                            int(ticker.df.iat[ticker.index_sell_deals[-1], 5] + ticker.outstanding_volumes)
                        ticker.outstanding_volumes = 0
                        start = False

                # вычесление прибыли и убытков
            ticker, error_arr, prof_per_year_dict, prof_rub_per_year_dict = \
                culc(ticker, error_arr, prof_per_year_dict, prof_rub_per_year_dict)
            # вычисление средней цены  оставшихся бумаг в рублях и валюте
            ticker, error_arr = outstanding_volume_price(ticker, error_arr)
            # сохранение для более простой проверки правильности расчетов
            path_to_save = path + '\\calc\\'
            formula_list = {'df': ticker.df, 'arr': [], 'name': ticker.ticker, 'path': path_to_save, 'columns': []}
            excel_saving(**formula_list)
            # заполнение таблицы
            TABLE_COLUMNS = [ticker.ticker,
                             int(ticker.total_buy),
                             int(ticker.total_sell),
                             int(ticker.outstanding_volumes),
                             round(ticker.prof_for_sold_securities_rub, 0),
                             round(ticker.prof_for_sold_securities, 0),
                             ticker.average_price_usd,
                             round(ticker.current_price, 2),
                             round(ticker.profit_for_outstanding_volumes, 0),
                             ticker.full_profit,
                             ticker.average_roe_for_outstanding_volumes,
                             ticker.broker,
                             ticker.currency,
                             ticker.full_name,
                             ticker.type]

            mytable.add_row(TABLE_COLUMNS)
            array_with_results.append(TABLE_COLUMNS)
            total_combined_profit = append_to_total_profit(ticker, total_combined_profit)
            # print(ticker.name, round(ticker.prof_for_sold_securities, 2))
            # print(ticker.name, total_combined_profit)

    # вывод результато
    output(mytable, total_combined_profit, prof_per_year_dict, prof_rub_per_year_dict)
    #сохранение результатов
    path_to_save = path + '\\results_'
    formula_list = {'df': pd.DataFrame(), 'arr': array_with_results, 'name': ticker.broker, 'path': path_to_save,
                    'columns': settings_for_sec.pretty_table_fields()}
    df_results = excel_saving(**formula_list)  # сохранение для иностранных бумаг

    # сохранение позиций с остаткоми
    path_to_save = path + '\\results_with_volumes'
    if not df_results.empty:
        df_results = df_results.loc[df_results['Остаток'] > 0]
        formula_list = {'df': df_results, 'arr': [], 'name': ticker.broker, 'path': path_to_save,
                        'columns': settings_for_sec.pretty_table_fields()}
        df_results = excel_saving(**formula_list)

    errors_df = pd.DataFrame(error_arr)
    errors_df.to_excel(path + f'ERRORS_{ticker.broker}.xls')


    return df_results


"""""
производится преобразования файла с сайта ВТБ в датафрейм, с последующей отправкой в main_func
"""""

if __name__ == '__main__':
    main_func()
