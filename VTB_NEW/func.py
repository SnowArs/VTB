from moex import ndfl_func, get_current_price
from class_new import Calculations
import math


def culc(ticker):
    print('начал выполнение culc функции')
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['Volume'][sale_row_number]
        bought_volume = ticker.buy_volume_array[0]
        diff_volume = bought_volume - sold_volume
        while not stop:
            if diff_volume == 0:
                ticker = profit_loss_calculation(ticker, 0, sale_row_number, sold_volume, diff_volume)
                ticker.buy_volume_array = ticker.buy_volume_array[1:]
                ticker.index_buy_deals = ticker.index_buy_deals[1:]
                break
            elif diff_volume > 0:
                ticker = profit_loss_calculation(ticker, 0, sale_row_number, sold_volume, diff_volume)
                ticker.buy_volume_array[0] = ticker.buy_volume_array[0] - sold_volume
                break
            else:  # отрицательный объем
                for i, buy_ind in enumerate(ticker.index_buy_deals):
                    if i == 0:
                        ticker = profit_loss_calculation(ticker, 1, sale_row_number, sold_volume, diff_volume, i)
                        negative_amount = diff_volume
                        ticker.buy_volume_array[0] = 0
                        index_to_del.append(i)
                    else:
                        diff = ticker.buy_volume_array[i] + negative_amount
                        ticker = profit_loss_calculation(ticker, 2, sale_row_number, -negative_amount, diff_volume, i)
                        if diff < 0:
                            negative_amount = diff
                            index_to_del.append(i)
                        elif diff > 0:
                            ticker.buy_volume_array[i] = ticker.buy_volume_array[i] + negative_amount
                            stop = True
                            break
                        else:
                            index_to_del.append(i)
                            ticker.buy_volume_array[i] = 0
                            stop = True
                            break
                ticker.buy_volume_array = ticker.buy_volume_array[len(index_to_del):]
                ticker.index_buy_deals = ticker.index_buy_deals[len(index_to_del):]
    if ticker.outstanding_volumes != sum(ticker.buy_volume_array):
        input(f"количество оставшихся бумаг {ticker.name} и полученных в результате подсчета не совпадают")
    print('закончил выполнение culc функции')
    return ticker


def profit_loss_calculation(ticker, option, sale_row_number, sold_volume, diff_volume, i=0):
    print('начал выполнение profit_loss_calculation функции')
    if option == 0:
        prof_loss_rur = ticker.df['RUB_sum'][sale_row_number] - \
                        sold_volume * ticker.df['ROE'][ticker.index_buy_deals[0]] * \
                        ticker.df['Price'][ticker.index_buy_deals[0]]
        prof_loss_usd = ticker.df['Sum'][sale_row_number] - \
                        sold_volume * ticker.df['Price'][ticker.index_buy_deals[0]] - \
                        ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]

    elif option == 1:
        prof_loss_rur = (sold_volume + diff_volume) / sold_volume * ticker.df['RUB_sum'][sale_row_number] - \
                        (sold_volume + diff_volume) * ticker.df['ROE'][i] * ticker.df['Price'][i]
        prof_loss_usd = (sold_volume + diff_volume) * ticker.df['Price'][sale_row_number] - (sold_volume + diff_volume) \
                        * ticker.df['Price'][i] - ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]

    else:
        prof_loss_rur = sold_volume * ticker.df['ROE'][sale_row_number] * ticker.df['Price'][sale_row_number] - \
                        sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['ROE'] * \
                        ticker.df.iloc[ticker.index_buy_deals[i]]['Price']
        prof_loss_usd = sold_volume * ticker.df['Price'][sale_row_number] - \
                        sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['Price'] - \
                        ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]

    ticker.ndfl = ndfl_func(prof_loss_rur) + ticker.ndfl
    ticker.profit_in_usd = prof_loss_usd + ticker.profit_in_usd

    ticker.df['profit_rus'][sale_row_number] = prof_loss_rur
    ticker.df['ndfl'][sale_row_number] = ticker.ndfl
    ticker.df['prof_usd'][sale_row_number] = prof_loss_usd

    print('закончил profit_loss_calculation')

    return ticker


def outstanding_volume_price(ticker):
    print('start outstanding_volume_price')
    sum_in_usd = 0
    sum_in_rub = 0
    if len(ticker.buy_volume_array) != 0:
        for number, line in enumerate(ticker.index_buy_deals):
            sum_in_usd = ticker.buy_volume_array[number] * ticker.df['Price'][line] + sum_in_usd
            sum_in_rub = ticker.buy_volume_array[number] * ticker.df['Price'][line] * \
                         ticker.df['ROE'][line] + sum_in_rub
        ticker.average_price_usd = sum_in_usd / sum(ticker.buy_volume_array)
        ticker.average_price_rub = sum_in_rub / sum(ticker.buy_volume_array)

        try:
            ticker.current_price = get_current_price(ticker.name)
            ticker.profit_for_outstanding_volumes = (ticker.current_price - ticker.average_price_usd) \
                                                    * ticker.outstanding_volumes
            ticker.total_profit = int(ticker.profit_in_usd + ticker.profit_for_outstanding_volumes - \
                                      ndfl_func(ticker.profit_for_outstanding_volumes))
            ticker.current_price = round(get_current_price(ticker.name), 1)
        except IndexError:
            ticker.profit_for_outstanding_volumes = 'N/A'
            ticker.total_profit = 'N/A'
            ticker.current_price = 'N/A'

    else:
        ticker.average_price_usd = 0
        ticker.profit_for_outstanding_volumes = 0
        ticker.average_price_rub = 0
        ticker.total_profit = int(ticker.profit_in_usd)
        ticker.current_price = get_current_price(ticker.name)
        print('закончил outstanding_volume_price')

    return ticker


def rub_securities_processing(ticker):
    print('start rub_securities_processing')
    if len(ticker.name) > 4:
        board = 'TQCB'
        market = 'bonds'
        ratio = 10
    else:
        board = 'TQBR'
        market = 'shares'
        ratio = 1

    ticker.average_buy = ticker.buy_sum_for_rub_securities / ticker.total_buy
    ticker.average_sell = ticker.sell_sum_for_rub_securities / ticker.total_sell
    ticker.current_price = Calculations.get_current_price_rur(ticker, board, market, ratio)
    if ticker.outstanding_volumes == 0:
        ticker.prof_loss_for_sold_securities = ticker.sell_sum_for_rub_securities - ticker.buy_sum_for_rub_securities
        ticker.profit_for_outstanding_volumes = 0
    elif math.isnan(ticker.average_sell):
        ticker.prof_loss_for_sold_securities = 0
        ticker.average_sell = 0
        ticker.profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes
    else:
        ticker.prof_loss_for_sold_securities = ticker.sell_sum_for_rub_securities - ticker.total_sell * ticker.average_buy
        ticker.profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes

    ticker.total_profit = ticker.prof_loss_for_sold_securities + ticker.profit_for_outstanding_volumes
    print('закончил rub_securities_processing')

    return ticker
