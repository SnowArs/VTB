import pandas as pd
from cbrf.models import DynamicCurrenciesRates
import datetime as dt


# функция подстановки ROE в таблицу
def fill_roe(roe_date, currency, date_min):
    print('fill_roe')
    date_min = date_min - dt.timedelta(days=1) * 10

    def roe_calc(date=roe_date):
        date_max = dt.datetime.now()
        roe_date_mod = pd.to_datetime(date, format='%Y-%m-%d', errors='coerce')

        if currency == 'USD':
            id_code = 'R01235'
            roe_ = 1
        elif currency == 'HKD':
            id_code = 'R01200'
            roe_ = 10
        elif currency == 'GBP':
            id_code = 'R01035'
            roe_ = 1
        else:
            id_code = 'R01239'
            roe_ = 1

        dynamic_rates = DynamicCurrenciesRates(date_min, date_max, id_code)

        return dynamic_rates.get_by_date(roe_date_mod).value / roe_

    if (currency == 'RUR') | (currency == 'RUB'):
        roe = 1
    else:
        try:
            roe = float(roe_calc())
        except AttributeError:
            i = True
            delta = dt.timedelta(days=1)
            roe_date_ = roe_date
            while i:
                roe_date_ = roe_date_ - delta
                try:
                    roe = float(roe_calc(roe_date_))
                    i = False
                except AttributeError:
                    continue
    # print(roe)
    return roe


# НДФЛ
def ndfl_func(profit):
    if profit > 0:
        ndfl = profit * 0.15
    else:
        ndfl = 0

    return ndfl
