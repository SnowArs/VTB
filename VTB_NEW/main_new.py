import warnings
from moex import *
import class_new
import os.path
from func import culc, outstanding_volume_price, rub_securities_processing

warnings.filterwarnings('ignore')


def append_to_total_profit(ticker, total_ndfl, total_combined_profit):
    total_ndfl += ticker.ndfl_full
    total_combined_profit += ticker.full_profit
    return total_ndfl, total_combined_profit


def excel_saving(**kwargs):
    if kwargs['df'].empty:
        df_to_save = pd.DataFrame(kwargs['arr'], columns=kwargs['columns'])
    else:
        df_to_save = kwargs['df']

    file_closed = True
    while file_closed:
        try:
            df_to_save.to_excel(f"{kwargs['path']}{kwargs['name']}.xls")
            file_closed = False
        except PermissionError:
            input(f"Необходимо закрыть файл {kwargs['path']}{kwargs['name']}.xls и нажать ENTER")
    return df_to_save


""""" 
1/ создаются таблицы для вывода в более читаемом выводе, чем вывод датафрейма
2/ 
"""""


def main_func(full_list_of_securities, df, broker):
    from prettytable import PrettyTable
    from prettytable import ALL
    total_ndfl_rus = 0
    total_ndfl_non_rus = 0
    total_combined_profit_rus = 0
    total_combined_profit_non_rus = 0
    error_arr = []

    # сознадние таблицы вывода
    mytable = PrettyTable()  # иностранные бумаги
    mytable_rus = PrettyTable()
    mytable_rus.hrules = ALL
    # имена полей таблицы
    field_names = ['Тикер', 'Куплено', 'Продано', 'Остаток', 'ндфл, руб', 'заф прибыль',
                   'средняя цена', 'текущая цена', 'потенциальная прибыль', 'общая прибыль']
    field_names_rus = field_names #дубли
    mytable.field_names = field_names
    mytable_rus.field_names = field_names_rus
    array_with_results = []
    array_with_results_rus = []
    """"" 
    2/ по каждой бумаге в портфеле производится подсчет показателей прибыльности
    """""
    for security in full_list_of_securities:
        print(f'processing {security}')
        df_for_security = df.loc[df.iloc[:, 1] == security].reset_index(drop=True)
        if df_for_security.empty:
            print(f'пустая датафрейм для  {security}')
            error_arr.append(security)
            continue
        else:
            ticker = class_new.Ticker(df_for_security, broker)
            ticker.df = pd.concat([ticker.df, pd.DataFrame(columns=['profit_rus', 'ndfl', 'prof_usd'])])

            # указание на ошибку если остаток акций отрицательный, скорее всего из-за сплита
            if (ticker.outstanding_volumes < 0) or (ticker.index_buy_deals.size == 0):
                print(f'похоже в позиции {ticker.name} проблемы с вычислениями, так как остаток отрицательный')
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
                error_arr.append(ticker.name)
            # ошибка пропущенных покупок, либо шорт
            elif (ticker.index_sell_deals.size > 0) and (ticker.index_buy_deals.size > 0):
                if ticker.index_sell_deals[0] < ticker.index_buy_deals[0]:
                    input(f'похоже в позиции {ticker.name} пропущены покупки, так как таблица начинается с продаж')
                    continue
            # обработка рублевых бумаг
            if ticker.currency == 'RUR':
                ticker, error_arr = rub_securities_processing(ticker, error_arr)
                path_to_save = 'calc\\'
                formula_list = {'df': ticker.df, 'arr': [], 'name': ticker.name, 'path': path_to_save, 'columns': []}
                excel_saving(**formula_list)
                RUS_TABLE_COLUMN = [ticker.name,
                                    ticker.total_buy,
                                    ticker.total_sell,
                                    ticker.outstanding_volumes,
                                    round(ticker.ndfl_full, 2),
                                    int(ticker.prof_for_sold_securities),
                                    round(ticker.average_buy, 2),
                                    ticker.current_price,
                                    int(ticker.profit_for_outstanding_volumes),
                                    int(ticker.full_profit)]
                mytable_rus.add_row(RUS_TABLE_COLUMN)
                total_ndfl_rus, total_combined_profit_rus = \
                    append_to_total_profit(ticker, total_ndfl_rus, total_combined_profit_rus)
                array_with_results_rus.append(RUS_TABLE_COLUMN)

            # блок вычисления прибыли и убытков по бумаге в USD/ EUR /HKD
            else:
                # вычесление прибыли и убытков
                ticker, error_arr = culc(ticker, error_arr)
                # вычисление средней цены  оставшихся бумаг в рублях и валюте
                ticker, error_arr = outstanding_volume_price(ticker, error_arr)
                # сохранение для более простой проверки правильности расчетов
                path_to_save = 'calc\\'
                formula_list = {'df': ticker.df, 'arr': [], 'name': ticker.name, 'path': path_to_save, 'columns': []}
                excel_saving(**formula_list)
                # заполнение таблицы
                NON_RUS_TABLE_COLUMNS = [ticker.name,
                                         ticker.total_buy,
                                         ticker.total_sell,
                                         ticker.outstanding_volumes,
                                         round(ticker.ndfl_full, 2),
                                         int(ticker.prof_for_sold_securities * ticker.exchange_to_usd),
                                         round(ticker.average_price_usd, 2),
                                         round(ticker.current_price, 2),
                                         round(ticker.profit_for_outstanding_volumes * ticker.exchange_to_usd, 2),
                                         int(ticker.full_profit * ticker.exchange_to_usd)]
                mytable.add_row(NON_RUS_TABLE_COLUMNS)
                array_with_results.append(NON_RUS_TABLE_COLUMNS + [ticker.average_roe_for_outstanding_volumes,
                                                                   ticker.broker, ticker.currency, ticker.full_name,
                                                                   ticker.type])
                total_ndfl_non_rus, total_combined_profit_non_rus = \
                    append_to_total_profit(ticker, total_ndfl_non_rus, total_combined_profit_non_rus)
    # сохранение результатов
    path_to_save = 'BD\\results_rus_'
    formula_list = {'df': pd.DataFrame(), 'arr': array_with_results_rus, 'name': broker, 'path': path_to_save,
                    'columns': field_names_rus}
    df_results_rus = excel_saving(**formula_list)
    path_to_save = 'BD\\results_'
    formula_list = {'df': pd.DataFrame(), 'arr': array_with_results, 'name': broker, 'path': path_to_save,
                    'columns': field_names + ['aver_ROE']}
    df_results = excel_saving(**formula_list)  # сохранение для иностранных бумаг
    # сохранение позиций с остаткоми
    path_to_save = 'BD\\results_rus_with_volumes'
    df_results_rus = df_results_rus.loc[df_results_rus['Остаток'] > 0]
    formula_list = {'df': df_results_rus, 'arr': [], 'name': broker, 'path': path_to_save,
                    'columns': field_names_rus}
    df_results_rus = excel_saving(**formula_list)

    path_to_save = 'BD\\results_with_volumes'
    df_results = df_results.loc[df_results['Остаток'] > 0]
    formula_list = {'df': df_results, 'arr': [], 'name': broker, 'path': path_to_save,
                    'columns': field_names + ['aver_ROE', 'брокер', 'валюта', 'название компании', 'признак']}


    errors_df = pd.DataFrame(error_arr)
    errors_df.to_excel(f'BD/ERRORS_{broker}.xls')

    print()
    print(mytable_rus)
    print(f'по рублевым бумагам прибыль: {int(total_combined_profit_rus)}')
    print()
    print(mytable)
    print(f'НДФЛ по всем иностранным бумагам в РУБ:  {int(total_ndfl_non_rus)},'
          f'общая прибыль по всем бумагам в USD: {int(total_combined_profit_non_rus)}')

    return df_results


""""" 
создание базы данных по курсам ЦБ для определнных валют и на определнную датуза, проверка новых дат,
заполнение колонок  ROE/RUB_sum
"""""


def filling_roe(_df, date_column, currency_column):
    _df = pd.concat([_df, pd.DataFrame(columns=['ROE_index'])])
    for _index, _row in _df.iterrows():
        _df['ROE_index'][_index] = _row[date_column].strftime('%Y-%m-%d') + '_' + _row[currency_column]

    if os.path.exists('BD\\roe_table.csv'):
        df_roe = pd.read_csv('BD\\roe_table.csv', usecols=['ROE_index', 'ROE'])
        _df = _df.merge(df_roe, how='left', left_on='ROE_index', right_on='ROE_index')
        _df.loc[_df.iloc[:, currency_column] == 'RUR', 'ROE'] = 1
        if _df.loc[_df['ROE'].isna()].empty:
            print('ROE по всем датам проставленно')
        else:
            for ind, line in _df.loc[_df['ROE'].isna()].iterrows():
                _df['ROE'][ind] = fill_roe(line[date_column], line[currency_column], _df.iloc[:, date_column].min())
                print(ind)
    else:
        for ind, line in _df.iterrows():
            _df = pd.concat([_df, pd.DataFrame(columns=['ROE'])])
            _df['ROE'][line] = fill_roe(line[date_column], line[currency_column], _df.iloc[:, date_column].min())
    _df2 = _df.loc[(_df['ROE'] != 1) & (_df.iloc[:, date_column] < dt.datetime.today().strftime('%Y-%m-%d')),
                   ['ROE_index', 'ROE']]
    _df2 = _df.drop_duplicates('ROE_index', ignore_index=True)
    df_roe = df_roe.append(_df2)# проверить логику появления df_roe
    df_roe = df_roe.drop_duplicates('ROE_index', ignore_index=True)
    df_roe.to_csv('BD\\roe_table.csv', index=False)

    _df['RUB_sum'] = _df['Sum'] * _df['ROE']
    _df = _df.astype({'ROE': 'float', 'RUB_sum': 'float'})
    return _df


"""""
производится преобразования файла с сайта ВТБ в датафрейм, с последующей отправкой в main_func
"""""


if __name__ == '__main__':
    main_func()
