def settings(broker):
    df_columns = ['date', 'ticker', 'buy_sell', 'currency', 'Price', 'Volume',
                'Commission', 'Sum', 'NKD', 'ROE_index', 'ROE', 'RUB_sum']
    if broker == 'IB':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'O', 'sell_code': 'C', 'Дата': 0}
    elif broker == 'VTB':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}
    elif broker == 'FRIDOM':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}
    elif broker == 'SBER':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}

    return sets, df_columns
