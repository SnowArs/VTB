import pandas as pd
import warnings
from main import main_func
from VTB_NEW.modules import roe_table_update

warnings.filterwarnings('ignore')


def vtb():
    df = pd.read_excel('BD\\VTB\\сделки_ВТБ_051121.xls', sheet_name='DealOwnsReport', header=3)
    df = df.loc[df['Тип сделки'] == 'Клиентская'].reset_index(drop=True)
    df['Код инструмента'] = df['Код инструмента'].str.replace('-', '_').str.split('_').str[0]
    # так как сделики в течении дня происходят разными строкам требуется группировка
    df = df.groupby(['Дата вал.', 'Код инструмента', 'B/S', 'Валюта']).agg(
        price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        volume=pd.NamedAgg(column='Кол-во', aggfunc='sum'),
        nkd=pd.NamedAgg(column='НКД', aggfunc='sum'),
        sum=pd.NamedAgg(column='Объем', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)
    df = roe_table_update(df, 0, 3)  # заполнение курса ЦБ по каждой из операций
    broker = 'VTB'
    df[['sec_type']] = ''
    df = df[['date', 'ticker', 'buy_sell', 'currency', 'price', 'volume',
             'commission', 'sum', 'nkd', 'sec_type', 'ROE_index', 'ROE', 'RUB_sum']]
    full_list_of_securities = df['Код инструмента'].unique().tolist()
    # full_list_of_securities = ['CHMF']
    main_func(full_list_of_securities, df, broker)
    return


if __name__ == '__main__':
    vtb()
