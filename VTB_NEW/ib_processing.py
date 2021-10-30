import csv

from VTB_NEW.modules import roe_table_update
from main import *
import warnings

warnings.filterwarnings('ignore')


def ib():

    file = r'BD\IB\U3557843_20210104_20211028.csv'
    # path = r'BD\IB'
    # file = modules.find_latest_file(path)
    with open(file, encoding='utf-8', newline='', errors='ignore') as File:
    # with open(file, newline='') as File:
        reader = csv.reader(File)
        first_deal = True
        first_open = True
        for row in reader:
            filter_ = ('Total', 'SubTotal', 'Header')
            if 'Сделки' in row and first_deal:
                df2021 = pd.DataFrame(columns=row)
                first_deal = False
            elif 'Открытые позиции' in row and first_open:
                df_check = pd.DataFrame(columns=row)
                first_open = False
            elif 'Сделки' in row and not first_deal:
                if not (set(filter_) & set(row)):
                    df2021.loc[len(df2021)] = row
            elif 'Открытые позиции' in row and not first_open:
                if not (set(filter_) & set(row)):
                    try:
                        df_check.loc[len(df_check)] = row
                    except ValueError:
                        print(f'ValueError {row}')
                        continue
    check_list_before_processing = df_check['Символ'].unique().tolist()
    df2021['date'] = df2021['Дата/Время'].str.split(',').str.get(0)
    df2021['date'] = pd.to_datetime(df2021['date'])
    df2021['B/S'] = df2021['Код'].str.split(';').str.get(0)
    df2021.loc[df2021['Количество'].str.contains(','), 'Количество'] = \
        df2021.loc[df2021['Количество'].str.contains(','), 'Количество'].str.replace(',', '')
    df2021 = df2021.astype({'Цена транзакции': 'float', 'Комиссия/плата': 'float', 'Выручка': 'float', 'Количество': 'float'})
    df2021['Количество'] = df2021['Количество'].abs()
    df2021['Выручка'] = df2021['Выручка'].abs()
    # df2021.loc[df2021['Символ'].endswith['%']] = df2021['Символ'].str.rsplit(' ', 1)
    df2021 = df2021.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена транзакции', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        Commission=pd.NamedAgg(column='Комиссия/плата', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Выручка', aggfunc='sum')
    )
    df2021.reset_index(drop=False, inplace=True)
    df2021 = roe_table_update(df2021, 0, 3)
    broker = 'IB'
    df2020 = pd.read_excel('BD\\IB\\ib2020.xls')
    df = df2020.append(df2021, ignore_index=True, sort=True)
    df = df.drop(df.loc[(df['B/S'] == '') | (df['B/S'].isna())].index)
    df = df[['date', 'Символ', 'B/S', 'Валюта', 'Price', 'Volume', 'Commission', 'Sum', 'ROE_index', 'ROE', 'RUB_sum']]
    df.loc[df['Символ'].str.endswith('%'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.endswith('%'), 'Символ'] = df['Символ'].str.rsplit('_', 1).str[0]
    df.loc[df['Символ'].str.endswith(' P'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.endswith(' C'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.contains('/'), 'Символ'] = df['Символ'].str.replace('/', '_')

    df.sort_values(by=['Символ', 'date'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    full_list_of_securities = df.iloc[:, 1].unique().tolist()
    exception_arr = ['OXY.WAR', 'WPG', 'SCO']
    # full_list_of_securities = ['MAC']
    # exception_arr = []
    full_list_of_securities = list(set(full_list_of_securities) ^ set(exception_arr))
    df_results = main_func(full_list_of_securities, df, broker)

    # проверка, что с остатками правильные бумаги
    df_results = df_results.loc[df_results['Остаток'] > 0]
    check_after_results = df_results['Тикер'].unique().tolist()
    missed_tickers = set(check_list_before_processing) ^ set(check_after_results)
    print(f'различия по бумагам с остатками в информации от брокера и после обработки : {missed_tickers}')
    return


if __name__ == '__main__':
    ib()
