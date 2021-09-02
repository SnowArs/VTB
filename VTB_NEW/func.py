from moex import ndfl_func
import math


def culc(ticker, error_array):
    # print('начал выполнение culc функции')
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['Volume'][sale_row_number]
        bought_volume = ticker.buy_volume_array[0]
        sold_volume_lef = bought_volume - sold_volume
        while not stop:
            if sold_volume_lef == 0:
                ticker = profit_calculation(ticker, 0, sale_row_number, sold_volume)
                ticker.buy_volume_array = ticker.buy_volume_array[1:]
                ticker.index_buy_deals = ticker.index_buy_deals[1:]
                break
            elif sold_volume_lef > 0:
                ticker = profit_calculation(ticker, 0, sale_row_number, sold_volume)
                ticker.buy_volume_array[0] = ticker.buy_volume_array[0] - sold_volume
                break
            elif sold_volume_lef < 0:  # отрицательный объем
                for i, buy_ind in enumerate(ticker.index_buy_deals):
                    if i == 0:
                        sold_volume_in_loop = ticker.buy_volume_array[0]
                        ticker = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop, i)
                        sold_volume_lef = sold_volume - sold_volume_in_loop
                        ticker.buy_volume_array[0] = 0
                        index_to_del.append(i)
                    else:
                        bought_amount_left = ticker.buy_volume_array[i] - sold_volume_lef
                        if bought_amount_left < 0:
                            sold_volume_in_loop = ticker.buy_volume_array[i]
                            ticker = profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop, i)
                            sold_volume_lef = sold_volume_lef - sold_volume_in_loop
                            index_to_del.append(i)
                        elif bought_amount_left > 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop, i)
                            ticker.buy_volume_array[i] = ticker.buy_volume_array[i] - sold_volume_lef
                            stop = True
                            break
                        elif bought_amount_left == 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker = profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop, i)
                            index_to_del.append(i)
                            ticker.buy_volume_array[i] = 0
                            stop = True
                            break
            ticker.buy_volume_array = ticker.buy_volume_array[len(index_to_del):]
            ticker.index_buy_deals = ticker.index_buy_deals[len(index_to_del):]
    if ticker.outstanding_volumes != sum(ticker.buy_volume_array):
        print(f"количество оставшихся бумаг {ticker.name} и полученных в результате подсчета не совпадают")
        error_array.append(ticker.name)
    # print('закончил выполнение culc функции')
    return ticker, error_array


def profit_calculation(ticker, option, sale_row_number, sold_volume, i=0):
    # print('начал выполнение profit_calculation функции')
    if option == 0:
        prof_rur = ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][ticker.index_buy_deals[0]] * \
                   ticker.df['Price'][ticker.index_buy_deals[0]]
        prof_usd = ticker.df['Sum'][sale_row_number] - \
                   sold_volume * ticker.df['Price'][ticker.index_buy_deals[0]] - \
                   ndfl_func(prof_rur) / ticker.df['ROE'][sale_row_number]

    elif option == 1:
        buy_row_number = ticker.index_buy_deals[i]
        prof_rur = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][buy_row_number] * ticker.df['Price'][buy_row_number]
        prof_usd = sold_volume * ticker.df['Price'][sale_row_number] - sold_volume \
                   * ticker.df['Price'][buy_row_number] - ndfl_func(prof_rur) / ticker.df['ROE'][
                       sale_row_number]

    elif option == 2:
        prof_rur = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['ROE'] * \
                   ticker.df.iloc[ticker.index_buy_deals[i]]['Price']
        prof_usd = sold_volume * ticker.df['Price'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['Price'] - \
                   ndfl_func(prof_rur) / ticker.df['ROE'][sale_row_number]

    ticker.ndfl = ndfl_func(prof_rur)
    ticker.ndfl_full += ticker.ndfl
    ticker.prof_for_sold_securities += prof_usd * ticker.exchange_to_usd
    row_to_fill = sale_row_number + i
    #проверка чтобы не было перезаписи вычислений
    if ticker.filled_row >= row_to_fill:
        row_to_fill = ticker.filled_row + 1
        ticker.filled_row = row_to_fill
    if ticker.df.shape[0] == row_to_fill:
        new_row = {'profit_rus': prof_rur, 'ndfl': ticker.ndfl, 'prof_usd': prof_usd}
        ticker.df = ticker.df.append(new_row, ignore_index=True)
    else:
        ticker.df['profit_rus'][row_to_fill] = prof_rur
        ticker.df['ndfl'][row_to_fill] = ticker.ndfl
        ticker.df['prof_usd'][row_to_fill] = prof_usd
    ticker.filled_row = row_to_fill
    # print('закончил profit_calculation')

    return ticker


def outstanding_volume_price(ticker, error_array):
    # print('start outstanding_volume_price')
    sum_in_usd = 0
    sum_in_rub = 0
    if len(ticker.buy_volume_array) != 0:
        for number, line in enumerate(ticker.index_buy_deals):
            sum_in_usd += ticker.buy_volume_array[number] * ticker.df['Price'][line]
            sum_in_rub += ticker.buy_volume_array[number] * ticker.df['Price'][line] * ticker.df['ROE'][line]
        ticker.average_roe_for_outstanding_volumes = round(sum_in_rub/sum_in_usd, 2)
        ticker.average_price_usd = \
            round(sum_in_rub/(ticker.average_roe_for_outstanding_volumes * sum(ticker.buy_volume_array)), 2)
        ticker.average_price_rub = round(sum_in_rub / sum(ticker.buy_volume_array), 2)
        try:
            ticker.profit_for_outstanding_volumes = (ticker.current_price - ticker.average_price_usd) \
                                                    * ticker.outstanding_volumes * ticker.exchange_to_usd
            ticker.full_profit = int(ticker.prof_for_sold_securities + ticker.profit_for_outstanding_volumes - \
                                     ndfl_func(ticker.profit_for_outstanding_volumes))
        except IndexError:
            ticker.profit_for_outstanding_volumes = 'N/A'
            ticker.full_profit = 'N/A'
            ticker.current_price = 'N/A'
    else:
        ticker.average_price_usd = 0
        ticker.profit_for_outstanding_volumes = 0
        ticker.average_price_rub = 0
        ticker.full_profit = int(ticker.prof_for_sold_securities)
        # print('закончил outstanding_volume_price')

    if ticker.outstanding_volumes != sum(ticker.buy_volume_array):
        print(f"количество оставшихся бумаг {ticker.name} и полученных в результате подсчета не совпадают")
        error_array.append(ticker.name)

    return ticker, error_array


def rub_securities_processing(ticker, error_array):
    # print('start rub_securities_processing')

    ticker.average_buy = ticker.buy_sum_for_rub_securities / ticker.total_buy
    ticker.average_sell = ticker.sell_sum_for_rub_securities / ticker.total_sell
    if ticker.outstanding_volumes == 0:
        prof_for_sold_securities = ticker.sell_sum_for_rub_securities - ticker.buy_sum_for_rub_securities
        ticker.prof_for_sold_securities = prof_for_sold_securities - ndfl_func(prof_for_sold_securities)
        profit_for_outstanding_volumes = 0
        ticker.profit_for_outstanding_volumes = 0
    elif math.isnan(ticker.average_sell):
        ticker.prof_for_sold_securities = 0
        ticker.average_sell = 0
        profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes
        ticker.profit_for_outstanding_volumes = profit_for_outstanding_volumes - \
                                                ndfl_func(profit_for_outstanding_volumes)
    else:
        prof_for_sold_securities = ticker.sell_sum_for_rub_securities - ticker.total_sell * ticker.average_buy
        ticker.prof_for_sold_securities = prof_for_sold_securities - ndfl_func(prof_for_sold_securities)
        profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes
        ticker.profit_for_outstanding_volumes = profit_for_outstanding_volumes - \
                                                ndfl_func(profit_for_outstanding_volumes)
    ticker.full_profit = ticker.prof_for_sold_securities + ticker.profit_for_outstanding_volumes
    ticker.ndfl_full = ndfl_func(profit_for_outstanding_volumes)

    # print('закончил rub_securities_processing')

    return ticker, error_array
