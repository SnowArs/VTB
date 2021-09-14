import pandas as pd


def load_names():
    df = pd.read_excel('BD\\Company_names.xls')
    df['Тикер'] = df['Тикер'].astype('str')
    return df
