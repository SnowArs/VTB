def settings(broker):
    if broker == 'IB':
        settings = {'name' : 1, 'buy_col' : 2, 'buy_code' : 'O', 'sell_code' : 'C', 'Дата': 0}
    elif broker == 'VTB':
        settings = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0, 'Commission': 0.001}
    elif broker == 'FRIDOM':
        settings = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}
    elif broker == 'SBER':
        settings = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа', 'Дата': 0}


    return settings