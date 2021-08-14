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

# df = pd.DataFrame()
import csv

with open('U3557843_20210101_20210811.csv', encoding='utf-8', newline='') as File:
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
            # if 'Total' not in row:
            #     if 'SubTotal' not in row:
            #         if 'Header' not in row:
            #             df.loc[len(df)] = row


df['date']=df['Дата/Время'].str.split(',').str.get(0)
df['B/S'] = df['Код'].str.split(';').str.get(0)
df = df.astype({'Цена транзакции': 'float', 'Комиссия/плата': 'float', 'Выручка': 'float'})
df = df.groupby(['date', 'Символ', 'B/S', 'Валюта']).agg(
    Price=pd.NamedAgg(column='Цена транзакции', aggfunc='mean'),
    Volume=pd.NamedAgg(column='Количество', aggfunc='sum'),
    Comisson=pd.NamedAgg(column='Комиссия/плата', aggfunc='sum'),
    Sum=pd.NamedAgg(column='Выручка', aggfunc='sum')
)
df.reset_index(drop=False, inplace=True)
input()
