import pandas as pd
import warnings
from main import main_func
from VTB_NEW.modules import roe_table_update
import settings
warnings.filterwarnings('ignore')


def sber():
    df = pd.read_excel('BD\\SBER\\Сделки_2015-01-01--2021-11-09.xlsx', sheet_name='Сделки', header=0)
    df = df[['Дата расчётов', 'Код финансового инструмента', 'Тип финансового инструмента',
             'Тип рынка', 'Операция', 'Количество', 'Цена', 'НКД', 'Объём сделки',
             'Валюта', 'Курс', 'Комиссия торговой системы', 'Комиссия банка',
             'Сумма зачисления/списания', 'Тип сделки']]
    df['Комиссия'] = df['Комиссия торговой системы'] + df['Комиссия банка']
    df['Дата расчётов'] = df['Дата расчётов'].dt.date
    # так как сделики в течении дня происходят разными строкам требуется группировка
    df = df.groupby(['Дата расчётов', 'Код финансового инструмента', 'Операция', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        NKD=pd.NamedAgg(column='НКД', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Объём сделки', aggfunc='sum'),
        Commission=pd.NamedAgg(column='Комиссия', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)
    df = roe_table_update(df, 0, 3)  # заполнение курса ЦБ по каждой из операций
    broker = 'SBER'
    df.rename(columns={'Дата расчётов' : 'date', 'Код финансового инструмента': 'ticker', 'Операция': 'buy_sell',
                       'Валюта': 'currency'}, inplace=True)
    df = df[['date', 'ticker', 'buy_sell', 'currency', 'Price', 'Volume',
                'Commission', 'Sum', 'NKD', 'ROE_index', 'ROE', 'RUB_sum']]
    # full_list_of_securities = df['Код финансового инструмента'].unique().tolist()
    exception_arr = ['26208^', 'MOEX', 'RU000A0ZZ547', 'CHMF', 'LSRG', 'MTSS', 'RU000A0JV8Q2', 'RU000A100YD8',
                     'RU000A0JWHA4', 'RU000A0ZYYN4', 'XS1383922876', 'XS1639490918']
    # full_list_of_securities = ['APTK']
    # exception_arr = []
    # full_list_of_securities = list(set(full_list_of_securities) ^ set(exception_arr))
    main_func(df, broker, exception_arr)
    return


if __name__ == '__main__':
    sber()
