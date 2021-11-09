def settings(broker):
    if broker == 'IB':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'O', 'sell_code': 'C', 'Дата': 0, 'Commission': 0.001}
    elif broker == 'VTB':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0, 'Commission': 0.001}
    elif broker == 'FRIDOM':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0, 'Commission': 0.006}
    elif broker == 'SBER':
        sets = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}

    return sets
