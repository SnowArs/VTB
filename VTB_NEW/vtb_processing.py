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
        Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Кол-во', aggfunc='sum'),
        NKD=pd.NamedAgg(column='НКД', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Объем', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)
    df = roe_table_update(df, 0, 3)  # заполнение курса ЦБ по каждой из операций
    broker = 'VTB'

    full_list_of_securities = df['Код инструмента'].unique().tolist()
    # full_list_of_securities = ['CHMF']
    main_func(full_list_of_securities, df, broker)
    return


if __name__ == '__main__':
    vtb()
