import pandas as pd
import warnings
from main import main_func
from VTB_NEW.modules import roe_table_update
import settings_for_sec
warnings.filterwarnings('ignore')


def fridom():
    df = pd.read_excel('BD\\FRIDOM\\FRIDOM 211221.xlsx')
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
    df = roe_table_update(df, 0, 3)
    df['broker'] = 'FRIDOM'
    df.rename(columns={'Символ': 'ticker', 'B/S': 'buy_sell', 'Валюта': 'currency'}, inplace=True)
    df[['nkd', 'sec_type']] = ''
    df = df[settings_for_sec.df_fields()]
    main_func(df)


if __name__ == '__main__':
    fridom()
