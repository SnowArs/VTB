import pandas as pd
import warnings
from main import main_func
from VTB_NEW.modules import roe_table_update

warnings.filterwarnings('ignore')


def fridom():
    df = pd.read_excel('BD\\FRIDOM\\FRIDOM 291021.xlsx')
    df['date'] = pd.to_datetime(df['Расчеты'])
    df['B/S'], df['Символ'], df['Валюта'] = df['Операция'], df['Тикер'], df['валюта']
    df['Символ'] = df['Символ'].str.replace('.', '_').str.split('_').str[0]

    df = df.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
        price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        commission=pd.NamedAgg(column='Комиссия', aggfunc='sum'),
        sum=pd.NamedAgg(column='Сумма', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)

    full_list_of_securities = df.iloc[:, 1].unique().tolist()
    # full_list_of_securities = ['MAC']
    df = roe_table_update(df, 0, 3)
    broker = 'FRIDOM'

    df.reset_index(drop=True, inplace=True)
    df.rename(columns={'Символ': 'ticker', 'B/S': 'buy_sell', 'Валюта': 'currency'}, inplace=True)
    df[['nkd', 'sec_type']] = ''
    df = df[['date', 'ticker', 'buy_sell', 'currency', 'price', 'volume',
             'commission', 'sum', 'nkd', 'sec_type', 'ROE_index', 'ROE', 'RUB_sum']]
    # df = df[['date', 'Символ', 'B/S', 'Валюта', 'Price', 'Volume', 'Commission', 'Sum', 'ROE_index', 'ROE', 'RUB_sum']]
    df.sort_values(by=['Символ', 'date'], inplace=True)
    main_func(full_list_of_securities, df, broker)


if __name__ == '__main__':
    fridom()
