# import warnings
#
# import pandas as pd
# from prettytable import PrettyTable
# from prettytable import ALL
# from moex import *
# import class_new
# import os.path
#
# warnings.filterwarnings('ignore')
#
# df = pd.read_csv('U3557843_20210101_20210811.csv', encoding='utf-8')
# input()
import pandas as pd
from main_new import filling_roe
import csv
from main_new import *

with open('ib.csv', encoding='utf-8', newline='') as File:
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

df['date']=df['Дата/Время'].str.split(',').str.get(0)
df['date'] = pd.to_datetime(df['date'])
df['B/S'] = df['Код'].str.split(';').str.get(0)
# df = df.astype({'Цена транзакции': 'float', 'Комиссия/плата': 'float', 'Выручка': 'float'})
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
df = filling_roe(df, 0, 3)
broker = 'IB'
ticker, mytable, mytable_rus, full_ndfl, full_prof_loss_usd, full_potential_profit, full_potential_profit_rus = \
        main_func(full_list_of_securities, df, broker)

print()
print(mytable_rus)
print(f'по рублевым бумагам прибыль: {int(full_potential_profit_rus)}')
print()
print(mytable)
print(f'НДФЛ по всем бумагам в РУБ:  {int(full_ndfl)},'
      f'общая прибыль по всем бумагам в USD: {int(full_potential_profit)}')

input()
