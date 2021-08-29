import pandas as pd
import warnings
from main_new import filling_roe, main_func

warnings.filterwarnings('ignore')

def main():
    df = pd.read_excel('BD\\FRIDOM.xlsx')
    df['date'] = pd.to_datetime(df['Расчеты'])
    df['B/S'], df['Символ'], df['Валюта'] = df['Операция'], df['Тикер'], df['валюта']
    df['Символ'] = df['Символ'].str.replace('.', '_').str.split('_').str[0]

    df = df.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        Comisson=pd.NamedAgg(column='Комиссия', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Сумма', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)

    full_list_of_securities = df.iloc[:, 1].unique().tolist()
    # full_list_of_securities = ['MAC']
    df = filling_roe(df, 0, 3)
    broker = 'FRIDOM'

    df.reset_index(drop=True, inplace=True)
    df = df[['date', 'Символ', 'B/S', 'Валюта', 'Price', 'Volume', 'Commission', 'Sum', 'ROE_index', 'ROE', 'RUB_sum']]
    main_func(full_list_of_securities, df, broker)


if __name__ == '__main__':
    main()
