import warnings
from moex import *
import class_new
import os.path
from func import culc, outstanding_volume_price, rub_securities_processing

warnings.filterwarnings('ignore')


def main_func(full_list_of_securities, df, broker):
    from prettytable import PrettyTable
    from prettytable import ALL
    full_ndfl = 0
    full_prof_loss_usd = 0
    full_potential_profit = 0
    full_potential_profit_rus = 0
    # сознадние таблицы вывода
    mytable = PrettyTable()  # иностранные бумаги
    mytable_rus = PrettyTable()
    mytable_rus.hrules = ALL
    # имена полей таблицы
    field_names = ['Тикер', 'Куплено', 'Продано', 'Остаток', 'НДФЛ, РУБ', 'Прибыль в USD',
                   'средняя цена', 'текущая цена', 'потенциальная прибыль', 'прибыль всех бумаг']
    mytable.field_names = field_names
    mytable_rus.field_names = field_names[0:4] + ['заф прибыль РУБ'] + field_names[7:]

    for security in full_list_of_securities:
        df_for_particular_security = df.loc[df.iloc[:, 1] == security].reset_index(drop=True)
        ticker = class_new.Ticker(df_for_particular_security, broker)
        # указание на ошибку если остаток акций отрицательный
        if ticker.outstanding_volumes < 0:
            print(f'похоже в позиции {ticker.name} проблемы с вычислениями, так как остаток отрицательный')
            continue
        # обработка рублевых бумаг
        if ticker.currency == 'RUR':
            ticker = rub_securities_processing(ticker)

            mytable_rus.add_row([ticker.name,
                                 ticker.total_buy,
                                 ticker.total_sell,
                                 ticker.outstanding_volumes,
                                 int(ticker.prof_loss_for_sold_securities_rus),
                                 ticker.current_price,
                                 int(ticker.profit_for_outstanding_volumes_rus),
                                 int(ticker.total_profit_rus)])

        # блок вычисления прибыли и убытков по бумаге в USD и EUR
        else:
            # вычесление прибыли и убытков
            ticker = culc(ticker)
            # вычисление средней цены  оставшихся бумаг в рублях и валюте
            ticker = outstanding_volume_price(ticker)
            # заполнение таблицы
            mytable.add_row([ticker.name,
                             ticker.total_buy,
                             ticker.total_sell,
                             ticker.outstanding_volumes,
                             int(ticker.ndfl),
                             int(ticker.profit_in_usd),
                             round(ticker.average_price_usd, 1),
                             round(ticker.current_price, 1),
                             round(ticker.profit_for_outstanding_volumes, 1),
                             int(ticker.total_profit)])

        full_ndfl = full_ndfl + ticker.ndfl
        full_prof_loss_usd = full_prof_loss_usd + ticker.profit_in_usd
        full_potential_profit = full_potential_profit + ticker.total_profit
        full_potential_profit_rus = full_potential_profit_rus + ticker.total_profit_rus

    return ticker, mytable, mytable_rus, full_ndfl, full_prof_loss_usd, full_potential_profit, full_potential_profit_rus


def filling_roe(_df, date_column, currency_column):
    _df = pd.concat([_df, pd.DataFrame(columns=['ROE_index'])])
    for _index, _row in _df.iterrows():
        _df['ROE_index'][_index] = _row[date_column].strftime('%Y-%m-%d') + '_' + _row[currency_column]

    # заполнение ROE/RUB_sum
    if os.path.exists('roe_table.csv'):
        df_roe = pd.read_csv('roe_table.csv', usecols=['ROE_index', 'ROE'])
        # df_roe['Дата вал.'] = df_roe['Дата вал.'].apply(pd.Timestamp)
        _df = _df.merge(df_roe, how='left', left_on='ROE_index', right_on='ROE_index')
        _df.loc[_df.iloc[:, currency_column] == 'RUR', 'ROE'] = 1
        # df_with_missed_roe
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
    _df2 = _df.loc[(_df['ROE'] != 1) & (_df.iloc[:, date_column] < dt.datetime.today().strftime('%Y-%m-%d')),\
                  ['ROE_index', 'ROE']]
    _df2 = _df.drop_duplicates('ROE_index', ignore_index=True)
    df_roe = df_roe.append(_df2)
    df_roe = df_roe.drop_duplicates('ROE_index', ignore_index=True)
    df_roe.to_csv('roe_table.csv', index=False)

    _df['RUB_sum'] = _df['Sum'] * _df['ROE']
    _df = _df.astype({'ROE': 'float', 'RUB_sum': 'float'})
    return _df


def main():
    df = pd.read_excel('сделки_ВТБ.xls', sheet_name='DealOwnsReport', header=3)
    df = df.loc[df['Тип сделки'] == 'Клиентская'].reset_index(drop=True)
    full_list_of_securities = df['Код инструмента'].unique().tolist()

    # группировка
    df = df.groupby(['Дата вал.', 'Код инструмента', 'B/S', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Кол-во', aggfunc='sum'),
        NKD=pd.NamedAgg(column='НКД', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Объем', aggfunc='sum')
    )

    df.reset_index(drop=False, inplace=True)
    # создание двух новых колонок с заполнением

    df = filling_roe(df, 0, 3)
    broker = 'VTB'

    ticker, mytable, mytable_rus, full_ndfl, full_prof_loss_usd, full_potential_profit, full_potential_profit_rus = \
        main_func(full_list_of_securities, df, broker)

    print()
    print(mytable_rus)
    print(f'по рублевым бумагам прибыль: {int(full_potential_profit_rus)}')
    print()
    print(mytable)
    print(f'НДФЛ по всем бумагам в РУБ:  {int(full_ndfl)},'
          f'общая прибыль по всем бумагам в USD: {int(full_potential_profit)}')


if __name__ == '__main__':
    main()
