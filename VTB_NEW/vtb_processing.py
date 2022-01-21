import pandas as pd
import warnings
from main import main_func
from VTB_NEW.modules import roe_table_update
import settings_for_sec
import socket

warnings.filterwarnings('ignore')

def path_search(broker_name):
    if socket.gethostname() == 'TABLET-LQ7125EI':
        main_dir = r'C:\Users\Ttt\OneDrive\Документы\securities_execution' + f'\{broker_name}'
        REPORTS_DIR = r'C:\Users\Ttt\OneDrive\Документы\WB_execution\weekly_reports_' + f'{broker_name}'
    else:
        main_dir = r'C:\Users\membe\OneDrive\Документы\securities_execution\VTB'
        REPORTS_DIR = r'C:\Users\membe\OneDrive\Документы\WB_execution\weekly_reports_' + f'{broker_name}'
    return main_dir


def vtb():
    broker = 'VTB'
    path_to_file = path_search(broker)
    df = pd.read_excel(f'{path_to_file}\сделки_ВТБ_190122.xls', sheet_name='DealOwnsReport', header=3)
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
    df.rename(columns={'Дата вал.': 'date', 'Код инструмента': 'ticker', 'B/S': 'buy_sell',
                       'Валюта': 'currency'}, inplace=True)
    df['broker'] = broker
    df[['sec_type', 'commission']] = ''
    df = df[settings_for_sec.df_fields()]
    main_func(df, path_to_file)
    return


if __name__ == '__main__':
    vtb()
