from moex import ndfl_func
import math
import settings


# подсчет купленных и проданных позиций по принципу FIFO
def culc(ticker, error_array, prof_per_year_dict, ndfl_per_year_dict):
    # print('начал выполнение culc функции')
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['Volume'][sale_row_number] * ticker.volume_mult
        try:
            bought_volume = ticker.buy_volume_array[0]
        except IndexError as e:
            print(f'Ошибка {e}')
            error_array.append(ticker.name)
            continue
        sold_volume_lef = bought_volume - sold_volume
        while not stop:
            if sold_volume_lef == 0:
                ticker, prof_per_year_dict, ndfl_per_year_dict \
                    = profit_calculation(ticker, 0, sale_row_number, sold_volume, prof_per_year_dict,
                                         ndfl_per_year_dict)
                ticker.buy_volume_array = ticker.buy_volume_array[1:]
                ticker.index_buy_deals = ticker.index_buy_deals[1:]
                break
            elif sold_volume_lef > 0:
                ticker, prof_per_year_dict, ndfl_per_year_dict \
                    = profit_calculation(ticker, 0, sale_row_number, sold_volume, prof_per_year_dict,
                                         ndfl_per_year_dict)
                ticker.buy_volume_array[0] = ticker.buy_volume_array[0] - sold_volume
                break
            elif sold_volume_lef < 0:  # отрицательный объем
                for i, buy_ind in enumerate(ticker.index_buy_deals):
                    if i == 0:
                        sold_volume_in_loop = ticker.buy_volume_array[0]
                        ticker, prof_per_year_dict, ndfl_per_year_dict \
                            = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop, prof_per_year_dict,
                                                 ndfl_per_year_dict, i)
                        sold_volume_lef = sold_volume - sold_volume_in_loop
                        ticker.buy_volume_array[0] = 0
                        index_to_del.append(i)
                    else:
                        bought_amount_left = ticker.buy_volume_array[i] - sold_volume_lef
                        if bought_amount_left < 0:
                            sold_volume_in_loop = ticker.buy_volume_array[i]
                            ticker, prof_per_year_dict, ndfl_per_year_dict =\
                                profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop, prof_per_year_dict,
                                                   ndfl_per_year_dict, i)
                            sold_volume_lef = sold_volume_lef - sold_volume_in_loop
                            index_to_del.append(i)
                        elif bought_amount_left > 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker, prof_per_year_dict, ndfl_per_year_dict \
                                = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop,
                                                     prof_per_year_dict, ndfl_per_year_dict, i)
                            ticker.buy_volume_array[i] = ticker.buy_volume_array[i] - sold_volume_lef
                            stop = True
                            break
                        elif bought_amount_left == 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker, prof_per_year_dict, ndfl_per_year_dict \
                                = profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop,
                                                     prof_per_year_dict, ndfl_per_year_dict, i)
                            index_to_del.append(i)
                            ticker.buy_volume_array[i] = 0
                            stop = True
                            break
                ticker.buy_volume_array = ticker.buy_volume_array[len(index_to_del):]
                ticker.index_buy_deals = ticker.index_buy_deals[len(index_to_del):]
                index_to_del = []
    if ticker.outstanding_volumes != sum(ticker.buy_volume_array):
        print(f"количество оставшихся бумаг {ticker.name} и полученных в результате подсчета не совпадают")
        error_array.append(ticker.name)

    # print('закончил выполнение culc функции')
    return ticker, error_array, prof_per_year_dict, ndfl_per_year_dict


# вычисление профита по каждой сделке в зависимости от остатка бумаг
def profit_calculation(ticker, option, sale_row_number, sold_volume, prof_per_year_dict, ndfl_per_year_dict, i=0):
    sets = settings.settings(ticker.broker)
    # print('начал выполнение profit_calculation функции')
    if option == 0:  # разница бумаг 0 или положительная
        commission = ticker.commission * ticker.df['RUB_sum'][sale_row_number] * sets['Commission']
        prof_rur = ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][ticker.index_buy_deals[0]] * \
                   ticker.df['Price'][ticker.index_buy_deals[0]] * ticker.bonds_mult - commission
        prof_usd = ticker.df['Sum'][sale_row_number] - \
                   sold_volume * ticker.df['Price'][ticker.index_buy_deals[0]] * ticker.bonds_mult - \
                   ndfl_func(prof_rur) / ticker.df['ROE'][sale_row_number]

    elif option == 1:  # разница бумаг отрицательная, первая итерация
        commission = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] \
                     * sets['Commission']
        buy_row_number = ticker.index_buy_deals[i]
        prof_rur = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][buy_row_number] * ticker.df['Price'][buy_row_number] - commission
        prof_usd = sold_volume * ticker.df['Price'][sale_row_number] - sold_volume * \
                   ticker.df['Price'][buy_row_number] - ndfl_func(prof_rur) / ticker.df['ROE'][
                       sale_row_number]

    elif option == 2:  # разница бумаг отрицательная, следующие  итерации
        commission = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] \
                     * sets['Commission']
        prof_rur = sold_volume / ticker.df['Volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['ROE'] * \
                   ticker.df.iloc[ticker.index_buy_deals[i]]['Price'] - commission
        prof_usd = sold_volume * ticker.df['Price'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['Price'] - \
                   ndfl_func(prof_rur) / ticker.df['ROE'][sale_row_number]

    ticker.ndfl = ndfl_func(prof_rur)
    ticker.ndfl_full += ticker.ndfl
    ticker.prof_for_sold_securities += prof_usd * ticker.exchange_to_usd
    row_to_fill = sale_row_number + i
    # проверка чтобы не было перезаписи вычислений в таблице каждой бумаги, чтобы проще делать проверку вычислений
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
    prof_per_year_dict[str(ticker.df.iloc[:, sets['Дата']][sale_row_number].year)].append(round(prof_usd, 2))
    ndfl_per_year_dict[str(ticker.df.iloc[:, sets['Дата']][sale_row_number].year)].append(round(ndfl_func(prof_rur), 2))
    return ticker, prof_per_year_dict, ndfl_per_year_dict


# подсчет прибыли по оставшимся бумагам. исходя из их средней цены и текущей цены
def outstanding_volume_price(ticker, error_array):
    # print('start outstanding_volume_price')
    sum_in_usd = 0
    sum_in_rub = 0
    if len(ticker.buy_volume_array) != 0:
        if ticker.current_price != 'N/A':
            for number, line in enumerate(ticker.index_buy_deals):
                sum_in_usd += ticker.buy_volume_array[number] * ticker.df['Price'][line]
                sum_in_rub += ticker.buy_volume_array[number] * ticker.df['Price'][line] * ticker.df['ROE'][line]
            ticker.average_roe_for_outstanding_volumes = round(sum_in_rub / sum_in_usd, 2)
            ticker.average_price_usd = \
                round(sum_in_rub / (ticker.average_roe_for_outstanding_volumes * sum(ticker.buy_volume_array)), 2)
            ticker.average_price_rub = round(sum_in_rub / sum(ticker.buy_volume_array), 2)
            try:
                ticker.profit_for_outstanding_volumes = round(((ticker.current_price - ticker.average_price_usd) *
                                                        ticker.outstanding_volumes * ticker.exchange_to_usd), 2)
                ticker.full_profit = round(ticker.prof_for_sold_securities + ticker.profit_for_outstanding_volumes -\
                                           ndfl_func(ticker.profit_for_outstanding_volumes), 2)
            except:
                ticker.profit_for_outstanding_volumes = 'N/A'
                ticker.full_profit = 'N/A'
                # ticker.current_price = 'N/A'
        else:
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


# расчет прибыли по российским бумагам, где нет валютной переоценки
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
        prof_for_sold_securities = 0
        ticker.prof_for_sold_securities = 0
        ticker.average_sell = 0
        profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes
        ticker.profit_for_outstanding_volumes = round(profit_for_outstanding_volumes - \
                                                ndfl_func(profit_for_outstanding_volumes), 2)
    else:
        prof_for_sold_securities = ticker.sell_sum_for_rub_securities - ticker.total_sell * ticker.average_buy
        ticker.prof_for_sold_securities = round(prof_for_sold_securities - ndfl_func(prof_for_sold_securities), 2)
        profit_for_outstanding_volumes = (ticker.current_price - ticker.average_buy) * ticker.outstanding_volumes

        ticker.profit_for_outstanding_volumes = round(profit_for_outstanding_volumes - \
                                                ndfl_func(profit_for_outstanding_volumes), 2)
    if math.isnan(ticker.profit_for_outstanding_volumes):
        ticker.profit_for_outstanding_volumes = 'N/A'
    else:
        ticker.full_profit = round(ticker.prof_for_sold_securities + ticker.profit_for_outstanding_volumes, 2)
    ticker.ndfl_full = ndfl_func(prof_for_sold_securities)

    # print('закончил rub_securities_processing')

    return ticker, error_array
