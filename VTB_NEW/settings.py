
def settings(broker):
    if broker == 'IB':
        settings = {'name' : 1, 'buy_col' : 2, 'buy_code' : 'O', 'sell_code' : 'C'}
    elif broker == 'VTB':
        settings = {'name': 1, 'buy_col': 2, 'buy_code': 'Покупка', 'sell_code': 'Продажа'}

    return settings

