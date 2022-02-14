import csv

from VTB_NEW.modules import roe_table_update
from main import *
import warnings
import settings_for_sec
from modules import path_search
warnings.filterwarnings('ignore')


def ib():
    broker = 'IB'
    path_to_main_dir = path_search()
    path_to_reports_from_brokers = f'{path_to_main_dir}\{broker}'
    file = path_to_reports_from_brokers + r'\U3557843_20220103_20220211.csv'

    with open(file, encoding='utf-8', newline='', errors='ignore') as File:
    # with open(file, newline='') as File:
        reader = csv.reader(File)
        first_deal = True
        first_open = True
        for row in reader:
            filter_ = ('Total', 'SubTotal', 'Header')
            if 'Сделки' in row and first_deal:
                df_current_year = pd.DataFrame(columns=row)
                first_deal = False
            elif 'Открытые позиции' in row and first_open:
                df_check = pd.DataFrame(columns=row)
                first_open = False
            elif 'Сделки' in row and not first_deal:
                if not (set(filter_) & set(row)):
                    df_current_year.loc[len(df_current_year)] = row
            elif 'Открытые позиции' in row and not first_open:
                if not (set(filter_) & set(row)):
                    try:
                        df_check.loc[len(df_check)] = row
                    except ValueError:
                        print(f'ValueError {row}')
                        continue
    check_list_before_processing = df_check['Символ'].unique().tolist()
    df_current_year['date'] = df_current_year['Дата/Время'].str.split(',').str.get(0)
    df_current_year['date'] = pd.to_datetime(df_current_year['date'])
    df_current_year['B/S'] = df_current_year['Код'].str.split(';').str.get(0)
    df_current_year.loc[df_current_year['Количество'].str.contains(','), 'Количество'] = \
        df_current_year.loc[df_current_year['Количество'].str.contains(','), 'Количество'].str.replace(',', '')
    df_current_year = df_current_year.astype({'Цена транзакции': 'float', 'Комиссия/плата': 'float', 'Выручка': 'float', 'Количество': 'float'})
    df_current_year['Количество'] = df_current_year['Количество'].abs()
    df_current_year['Выручка'] = df_current_year['Выручка'].abs()
    # df_current_year.loc[df_current_year['Символ'].endswith['%']] = df_current_year['Символ'].str.rsplit(' ', 1)
    df_current_year = df_current_year.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
        price=pd.NamedAgg(column='Цена транзакции', aggfunc='mean'),
        volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        commission=pd.NamedAgg(column='Комиссия/плата', aggfunc='sum'),
        sum=pd.NamedAgg(column='Выручка', aggfunc='sum')
    )
    df_current_year.reset_index(drop=False, inplace=True)
    df_current_year = roe_table_update(df_current_year, 0, 3)

    df_prev_years = pd.read_excel(path_to_main_dir + f'\\{broker}\\ib20-21.xlsx')
    df = df_prev_years.append(df_current_year, ignore_index=True)
    #Если надо сохранить новый год, то небоходимо раскомментировать нижний текст с указанием нового имени файла
    # df.sort_values(by=['Символ', 'date'], inplace=True)
    # df.to_excel(path_to_main_dir + f'\\{broker}\\ib20-21.xlsx', index=False)

    df = df.drop(df.loc[(df['B/S'] == '') | (df['B/S'].isna())].index)
    df = df[['date', 'Символ', 'B/S', 'Валюта', 'price', 'volume', 'commission', 'sum', 'ROE_index', 'ROE', 'RUB_sum']]
    df.loc[df['B/S'].str.contains('O'), 'B/S'] = df['B/S'].str.replace('O', 'Покупка')
    df.loc[df['B/S'].str.contains('C'), 'B/S'] = df['B/S'].str.replace('C', 'Продажа')
    df.loc[df['Символ'].str.endswith('%'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.endswith('%'), 'Символ'] = df['Символ'].str.rsplit('_', 1).str[0]
    df.loc[df['Символ'].str.endswith(' P'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.endswith(' C'), 'Символ'] = df['Символ'].str.replace(' ', '_')
    df.loc[df['Символ'].str.contains('/'), 'Символ'] = df['Символ'].str.replace('/', '_')

    df.sort_values(by=['Символ', 'date'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    exception_arr = ['OXY.WAR', 'WPG', 'SCO', 'CLNY PRJ']
    # exception_arr = []
    df['broker'] = 'IB'
    df.rename(columns={'Дата вал.': 'date', 'Символ': 'ticker', 'B/S': 'buy_sell',
                       'Валюта': 'currency'}, inplace=True)
    df[['nkd', 'sec_type']] = ''
    df = df[settings_for_sec.df_fields()]
    df_results = main_func(df, path_to_main_dir, exception_arr)

    # проверка, что с остатками правильные бумаги
    df_results = df_results.loc[df_results['Остаток'] > 0]
    check_after_results = df_results['Тикер'].unique().tolist()
    missed_tickers = set(check_list_before_processing) ^ set(check_after_results)
    print(f'различия по бумагам с остатками в информации от брокера и после обработки : {missed_tickers}')
    return


if __name__ == '__main__':
    ib()
