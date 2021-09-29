import pandas as pd
from modules import excel_saving


def load_names():
    df = pd.read_excel('BD\\Company_names.xlsx')
    df['Тикер'] = df['Тикер'].astype('str')
    return df


def update_bd_with_names(ticker):
    df = pd.read_excel('BD\\Company_names.xlsx')
    row = {'Тикер': ticker.name, 'Название компании': ticker.full_name, 'Брокер': ticker.broker,
           'Валюта': ticker.currency, 'Инструмент': ticker.type}
    df.loc[len(df)] = row
    path_to_save = 'BD\\'
    formula_list = {'df': df, 'arr': [], 'name': 'Company_names', 'path': path_to_save, 'columns': []}
    excel_saving(**formula_list)
