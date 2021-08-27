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


""""" 
1/ создаются таблицы для вывода в более читаемом выводе, чем вывод датафрейма
2/ 
"""""


def main_func(full_list_of_securities, df, broker, error_arr=[]):
    from prettytable import PrettyTable
    from prettytable import ALL
    total_ndfl_rus = 0
    total_ndfl_non_rus = 0
    total_combined_profit_rus = 0
    total_combined_profit_non_rus = 0

    # сознадние таблицы вывода
    mytable = PrettyTable()  # иностранные бумаги
    mytable_rus = PrettyTable()
    mytable_rus.hrules = ALL
    # имена полей таблицы
    field_names = ['Тикер', 'Куплено', 'Продано', 'Остаток', 'НДФЛ, РУБ', 'Прибыль в USD',
                   'средняя цена', 'текущая цена', 'потенциальная прибыль', 'прибыль всех бумаг']
    mytable.field_names = field_names
    mytable_rus.field_names = field_names[0:4] + ['заф прибыль РУБ'] + field_names[7:]
    array_with_results = []
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
                            int(ticker.df.iat[ticker.index_sell_deals[-1], 5] + \
                                ticker.outstanding_volumes)
                        ticker.outstanding_volumes = 0
                        start = False
                error_arr.append(ticker.name)
            # ошибка пропущенных покупок, либо шорт
            elif (ticker.index_sell_deals.size > 0) and (ticker.index_buy_deals.size > 0):
                if (ticker.index_sell_deals[0] < ticker.index_buy_deals[0]):
                    input(f'похоже в позиции {ticker.name} пропущены покупки, так как таблица начинается с продаж')
                    continue
            # обработка рублевых бумаг
            if ticker.currency == 'RUR':
                ticker, errors = rub_securities_processing(ticker, error_arr)

                RUS_TABLE_COLUMN = [ticker.name,
                                    ticker.total_buy,
                                    ticker.total_sell,
                                    ticker.outstanding_volumes,
                                    int(ticker.prof_for_sold_securities),
                                    ticker.current_price,
                                    int(ticker.profit_for_outstanding_volumes),
                                    int(ticker.full_profit)]
                mytable_rus.add_row(RUS_TABLE_COLUMN)
                total_ndfl_rus, total_combined_profit_rus =\
                    append_to_total_profit(ticker, total_ndfl_rus, total_combined_profit_rus)
            # блок вычисления прибыли и убытков по бумаге в USD/ EUR /HKD
            else:
                # вычесление прибыли и убытков
                ticker, errors = culc(ticker, error_arr)
                # сохранение для более простой проверки правильности расчетов
                ticker.df.to_excel(f'calc\\{ticker.name}.xls')
                # вычисление средней цены  оставшихся бумаг в рублях и валюте
                ticker = outstanding_volume_price(ticker)
                # заполнение таблицы
                NON_RUS_TABLE_COLUMNS = [ticker.name,
                                         ticker.total_buy,
                                         ticker.total_sell,
                                         ticker.outstanding_volumes,
                                         round(ticker.ndfl_full, 2),
                                         int(ticker.prof_for_sold_securities * ticker.exchange_to_usd),
                                         round(ticker.average_price_usd, 1),
                                         round(ticker.current_price, 1),
                                         round(ticker.profit_for_outstanding_volumes * ticker.exchange_to_usd, 1),
                                         int(ticker.full_profit * ticker.exchange_to_usd)]
                mytable.add_row(NON_RUS_TABLE_COLUMNS)
                array_with_results.append(NON_RUS_TABLE_COLUMNS+[ticker.average_roe_for_outstanding_volumes])
                total_ndfl_non_rus, total_combined_profit_non_rus =\
                    append_to_total_profit(ticker, total_ndfl_non_rus, total_combined_profit_non_rus)

    df_with_results = pd.DataFrame(array_with_results, columns=field_names+['aver_ROE'])

    file_closed = True
    while file_closed:
        try:
            df_with_results.to_excel(f'BD\\results_{broker}.xls')
            file_closed = False
        except PermissionError:
            input(f'Необходимо закрыть файл results_{broker}.xls и нажать ENTER')

    errors_df = pd.DataFrame(errors)
    errors_df.to_excel(f'BD/ERRORS_{broker}.xls')

    print()
    print(mytable_rus)
    print(f'по рублевым бумагам прибыль: {int(total_combined_profit_rus)}')
    print()
    print(mytable)
    print(f'НДФЛ по всем иностранным бумагам в РУБ:  {int(total_ndfl_non_rus)},'
          f'общая прибыль по всем бумагам в USD: {int(total_combined_profit_non_rus)}')
    return


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
    _df2 = _df.loc[(_df['ROE'] != 1) & (_df.iloc[:, date_column] < dt.datetime.today().strftime('%Y-%m-%d')), \
                   ['ROE_index', 'ROE']]
    _df2 = _df.drop_duplicates('ROE_index', ignore_index=True)
    df_roe = df_roe.append(_df2)
    df_roe = df_roe.drop_duplicates('ROE_index', ignore_index=True)
    df_roe.to_csv('BD\\roe_table.csv', index=False)

    _df['RUB_sum'] = _df['Sum'] * _df['ROE']
    _df = _df.astype({'ROE': 'float', 'RUB_sum': 'float'})
    return _df


"""""
производится преобразования файла с сайта ВТБ в датафрейм, с последующей отправкой в main_func
"""""


def main():
    df = pd.read_excel('BD\\сделки_ВТБ.xls', sheet_name='DealOwnsReport', header=3)
    df = df.loc[df['Тип сделки'] == 'Клиентская'].reset_index(drop=True)
    full_list_of_securities = df['Код инструмента'].unique().tolist()
    # full_list_of_securities = ['COG']

    # так как сделики в течении дня происходят разными строкам требуется группировка
    df = df.groupby(['Дата вал.', 'Код инструмента', 'B/S', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Кол-во', aggfunc='sum'),
        NKD=pd.NamedAgg(column='НКД', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Объем', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)
    df = filling_roe(df, 0, 3)  # заполнение курса ЦБ по каждой из операций
    broker = 'VTB'
    main_func(full_list_of_securities, df, broker)
    return


if __name__ == '__main__':
    main()
