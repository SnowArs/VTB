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
        total_combined_profit += ticker.full_profit
    return total_combined_profit


""""" 
1/ создаются таблицы для вывода в более читаемом выводе, чем вывод датафрейма
2/ 
"""""


def main_func(df, exception_arr=[]):
    df_for_execution = df.loc[~df.ticker.isin(exception_arr)].reset_index(drop=True)


    # выделяем отдельно рублевые бумаги для получения цены через сайт МБ
    full_list_of_securities_rub = set(df_for_execution.loc[df_for_execution.currency.str.contains('RUB', 'RUR')].ticker)
    df_sec_prices_rub = pd.DataFrame(sec_prices_rub.current_prices(list(full_list_of_securities_rub)),
                                     columns=['ticker', 'name', 'cur_price'])
    # выделяем отдельно валютные бумаги для получения цены через сайт yahoo (отдельная история с GBP и HKD)
    full_list_of_securities_non_rub = set(df_for_execution.loc[~df_for_execution.currency.str.contains('RUB', 'RUR')].
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
    df_without_name_and_prices = df_for_execution.loc[df_for_execution.name == '']

    for index, row in df_without_name_and_prices.iterrows():
        name = class_new.Ticker.security_name(row)
        print(name)
        if name == row.ticker:
            continue
        else:
            ticker, name, price = asynco_new.main(name)
            print(name)
        # df_for_execution['exec_ticker'] = ''

    # сознадние таблицы вывода
    mytable = PrettyTable()
    # имена полей таблицы
    mytable.field_names = settings_for_sec.pretty_table_fields()

    total_combined_profit = 0
    error_arr = []
    array_with_results = []
    prof_per_year_dict = {'2018': [], '2019': [], '2020': [], '2021': []}
    prof_rub_per_year_dict = {'2018': [], '2019': [], '2020': [], '2021': []}

    """"" 
    2/ по каждой бумаге в портфеле производится подсчет показателей прибыльности
    """""
    for security in ['RU000A100V61']:#sorted(full_list_of_securities):
        print(f'processing {security}')
        df_for_security = df_for_execution.loc[df_for_execution.ticker == security].reset_index(drop=True)
        # security_name_and_price = \
        #     list(df_for_execution.loc[df_for_execution.ticker == security].values[0])

        if df_for_security.empty:  # проверка на пустую таблицу по инструменту
            print(f'пустая датафрейм для  {security}')
            error_arr.append(security)
            continue
        else:
            ticker = class_new.Ticker(df_for_security, df_with_currencies_exchange)
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
            path_to_save = 'calc\\'
            formula_list = {'df': ticker.df, 'arr': [], 'name': ticker.ticker, 'path': path_to_save, 'columns': []}
            excel_saving(**formula_list)
            # заполнение таблицы
            TABLE_COLUMNS = [ticker.ticker,
                             ticker.total_buy,
                             ticker.total_sell,
                             ticker.outstanding_volumes,
                             round(ticker.prof_for_sold_securities_rub, 2),
                             round(ticker.prof_for_sold_securities, 2),
                             ticker.average_price_usd,
                             ticker.current_price,
                             ticker.profit_for_outstanding_volumes,
                             ticker.full_profit,
                             ticker.average_roe_for_outstanding_volumes,
                             ticker.broker,
                             ticker.currency,
                             ticker.full_name,
                             ticker.type]

            mytable.add_row(TABLE_COLUMNS)
            array_with_results.append(TABLE_COLUMNS)
            total_combined_profit = append_to_total_profit(ticker, total_combined_profit)

    path_to_save = 'BD\\results_'
    formula_list = {'df': pd.DataFrame(), 'arr': array_with_results, 'name': ticker.broker, 'path': path_to_save,
                    'columns': settings_for_sec.pretty_table_fields()}
    df_results = excel_saving(**formula_list)  # сохранение для иностранных бумаг

    # сохранение позиций с остаткоми
    path_to_save = 'BD\\results_with_volumes'
    df_results = df_results.loc[df_results['Остаток'] > 0]
    formula_list = {'df': df_results, 'arr': [], 'name': ticker.broker, 'path': path_to_save,
                    'columns': settings_for_sec.pretty_table_fields()}
    df_results = excel_saving(**formula_list)

    errors_df = pd.DataFrame(error_arr)
    errors_df.to_excel(f'BD/ERRORS_{ticker.broker}.xls')

    print()
    print(mytable)
    print(f'общая прибыль по всем бумагам в USD до уплаты налогов: {int(total_combined_profit)}')

    print(f'year 2020 - profit от закрытых сделок -  {round(sum(prof_per_year_dict["2020"]), 2)}, '
          f'year 2021 - profit от закрытых сделок - {round(sum(prof_per_year_dict["2021"]), 2)} ')

    print(f'year 2020 - НДФЛ по закрытым сделкам - {round(sum(prof_rub_per_year_dict["2020"]) * 0.15, 2)}, '
          f'year 2021 - НДФЛ по закрытым сделкам {round(sum(prof_rub_per_year_dict["2021"]) * 0.15, 2)} ')

    return df_results


"""""
производится преобразования файла с сайта ВТБ в датафрейм, с последующей отправкой в main_func
"""""

if __name__ == '__main__':
    main_func()
