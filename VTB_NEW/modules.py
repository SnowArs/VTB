import datetime as dt
import os

import pandas
import pandas as pd

from VTB_NEW.moex import fill_roe


def find_latest_file(path):
    files = os.listdir(path)
    if files:
        files = [os.path.join(path, file) for file in files]
        files = [file for file in files if os.path.isfile(file)]

        latest_file = max(files, key=os.path.getatime)
        return latest_file


""""" 
создание базы данных по курсам ЦБ для определнных валют и на определнную датуза, проверка новых дат,
заполнение колонок  ROE/RUB_sum
"""""


def roe_table_update(df, date_column, currency_column):
    df = pd.concat([df, pd.DataFrame(columns=['ROE_index'])])
    for _index, _row in df.iterrows():
        df['ROE_index'][_index] = _row[date_column].strftime('%Y-%m-%d') + '_' + _row[currency_column]

    if os.path.exists('BD\\roe_table.csv'):
        df_roe = pd.read_csv('BD\\roe_table.csv', usecols=['ROE_index', 'ROE'])
        df = df.merge(df_roe, how='left', left_on='ROE_index', right_on='ROE_index')
        df.loc[df.iloc[:, currency_column].str.contains('RUR' or 'RUB'), 'ROE'] = 1
        if df.loc[df['ROE'].isna()].empty:
            print('ROE по всем датам проставленно')
        else:
            for ind, line in df.loc[df['ROE'].isna()].iterrows():
                if ('RUR' or 'RUB') in df['Валюта'][ind]:
                    df['ROE'][ind] = 1
                else:
                    df['ROE'][ind] = fill_roe(line[date_column], line[currency_column], df.iloc[:, date_column].min())
                print(ind)
    else:
        for ind, line in df.iterrows():
            df = pd.concat([df, pd.DataFrame(columns=['ROE'])])
            df['ROE'][line] = fill_roe(line[date_column], line[currency_column], df.iloc[:, date_column].min())
            df_roe = pd.DataFrame(columns=['ROE_index', 'ROE'])
    df2 = df.loc[(df['ROE'] != 1) & (df.iloc[:, date_column].astype('str') < dt.datetime.today().strftime('%Y-%m-%d')),
                 ['ROE_index', 'ROE']]
    df2 = df2.drop_duplicates('ROE_index', ignore_index=True)
    df_roe = df_roe.append(df2)  # проверить логику появления df_roe
    df_roe = df_roe.drop_duplicates('ROE_index', ignore_index=True)
    df_roe.to_csv('BD\\roe_table.csv', index=False)

    df['RUB_sum'] = df['Sum'] * df['ROE']
    df = df.astype({'ROE': 'float', 'RUB_sum': 'float'})
    return df


def excel_saving(**kwargs):
    if kwargs['df'].empty & (kwargs['arr'] == []):
        return
    else:
        if kwargs['df'].empty:
            df_to_save = pd.DataFrame(kwargs['arr'], columns=kwargs['columns'])
        else:
            df_to_save = kwargs['df']

        file_closed = True
        while file_closed:
            try:
                df_to_save.to_excel(f"{kwargs['path']}{kwargs['name']}.xlsx", float_format="%.2f", index=False)
                file_closed = False
            except PermissionError:
                input(f"Необходимо закрыть файл {kwargs['path']}{kwargs['name']}.xlsx и нажать ENTER")
    return df_to_save
