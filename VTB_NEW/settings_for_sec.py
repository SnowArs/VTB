def df_fields():
    fields = ['date', 'ticker', 'buy_sell', 'currency', 'price', 'volume',
              'commission', 'sum', 'nkd', 'sec_type', 'broker', 'ROE_index', 'ROE', 'RUB_sum']
    return fields


def pretty_table_fields():
    field_ = ['Тикер', 'Куплено', 'Продано', 'Остаток', 'заф прибыль РУБ', 'заф прибыль, USD ', 'средняя цена',
              'текущая цена', 'потенциальная прибыль', 'общая прибыль', 'средний ROE', 'брокер', 'валюта',
              'полное название', 'тип бумаги']

    return field_


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
