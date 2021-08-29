import csv
from main_new import *
import warnings

warnings.filterwarnings('ignore')


def main():
    with open('BD\\ib.csv', encoding='utf-8', newline='') as File:
        reader = csv.reader(File)
        first = True
        for row in reader:
            filter_ = ('Total', 'SubTotal', 'Header')
            if 'Сделки' in row and first:
                df = pd.DataFrame(columns=row)
                first = False
            elif 'Сделки' in row and not first:
                if not (set(filter_) & set(row)):
                    df.loc[len(df)] = row

    df['date'] = df['Дата/Время'].str.split(',').str.get(0)
    df['date'] = pd.to_datetime(df['date'])
    df['B/S'] = df['Код'].str.split(';').str.get(0)
    df.loc[df['Количество'].str.contains(','), 'Количество'] = \
        df.loc[df['Количество'].str.contains(','), 'Количество'].str.replace(',', '')
    df = df.astype({'Цена транзакции': 'float', 'Комиссия/плата': 'float', 'Выручка': 'float', 'Количество': 'float'})
    df['Количество'] = df['Количество'].abs()
    df['Выручка'] = df['Выручка'].abs()
    df = df.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
        Price=pd.NamedAgg(column='Цена транзакции', aggfunc='mean'),
        Volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
        Comisson=pd.NamedAgg(column='Комиссия/плата', aggfunc='sum'),
        Sum=pd.NamedAgg(column='Выручка', aggfunc='sum')
    )
    df.reset_index(drop=False, inplace=True)

    full_list_of_securities = df.iloc[:, 1].unique().tolist()
    # full_list_of_securities = ['MAC']
    df = filling_roe(df, 0, 3)
    broker = 'IB'
    df2020 = pd.read_excel('BD\\ib2020.xls')
    df = df2020.append(df, ignore_index=True, sort=True)
    df = df.drop(df.loc[df['B/S'] == ''].index)
    df.reset_index(drop=True, inplace=True)
    df = df[['date', 'Символ', 'B/S', 'Валюта', 'Price', 'Volume', 'Commission', 'Sum', 'ROE_index', 'ROE', 'RUB_sum']]
    main_func(full_list_of_securities, df, broker)
    return


if __name__ == '__main__':
    main()
