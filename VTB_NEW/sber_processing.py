import pandas as pd
import warnings
from main_new import main_func
from VTB_NEW.modules import roe_table_update

warnings.filterwarnings('ignore')


def sber():
    df = pd.read_excel('BD\\SBER\\Сделки_2015-01-01--2021-08-20.xlsx', sheet_name='Сделки', header=0)
    df = df[['Дата расчётов', 'Код финансового инструмента', 'Тип финансового инструмента',
             'Тип рынка', 'Операция', 'Количество', 'Цена', 'НКД', 'Объём сделки',
             'Валюта', 'Курс', 'Комиссия торговой системы', 'Комиссия банка',
             'Сумма зачисления/списания', 'Тип сделки']]
    df['Комиссия'] = df['Комиссия торговой системы'] + df['Комиссия банка']
    # df['Дата расчётов'] = df['Дата расчётов'].str.split('_').str[0]
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
    broker = 'VTB'
    full_list_of_securities = df['Код инструмента'].unique().tolist()
    # full_list_of_securities = ['FTCH']
    main_func(full_list_of_securities, df, broker)
    return


if __name__ == '__main__':
    sber()
