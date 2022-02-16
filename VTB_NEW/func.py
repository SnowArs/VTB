import math
import settings_for_sec


# подсчет купленных и проданных позиций по принципу FIFO
def culc(ticker, error_array, prof_per_year_dict, prof_rub_per_year_dict):
    # print('начал выполнение culc функции')
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['volume'][sale_row_number] * ticker.volume_mult
        try:
            bought_volume = ticker.buy_volume_array[0]
        except IndexError as e:
            print(f'Ошибка {e}')
            error_array.append(ticker.ticker)
            continue
        sold_volume_lef = bought_volume - sold_volume
        while not stop:
            if sold_volume_lef == 0:
                ticker, prof_per_year_dict, prof_rub_per_year_dict \
                    = profit_calculation(ticker, 0, sale_row_number, sold_volume, prof_per_year_dict,
                                         prof_rub_per_year_dict)
                ticker.buy_volume_array = ticker.buy_volume_array[1:]
                ticker.index_buy_deals = ticker.index_buy_deals[1:]
                break
            elif sold_volume_lef > 0:
                ticker, prof_per_year_dict, prof_rub_per_year_dict \
                    = profit_calculation(ticker, 0, sale_row_number, sold_volume, prof_per_year_dict,
                                         prof_rub_per_year_dict)
                ticker.buy_volume_array[0] = ticker.buy_volume_array[0] - sold_volume
                break
            elif sold_volume_lef < 0:  # отрицательный объем
                for i, buy_ind in enumerate(ticker.index_buy_deals):
                    if i == 0:
                        sold_volume_in_loop = ticker.buy_volume_array[0]
                        ticker, prof_per_year_dict, prof_rub_per_year_dict \
                            = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop, prof_per_year_dict,
                                                 prof_rub_per_year_dict, i)
                        sold_volume_lef = sold_volume - sold_volume_in_loop
                        ticker.buy_volume_array[0] = 0
                        index_to_del.append(i)
                    else:
                        bought_amount_left = ticker.buy_volume_array[i] - sold_volume_lef
                        if bought_amount_left < 0:
                            sold_volume_in_loop = ticker.buy_volume_array[i]
                            ticker, prof_per_year_dict, prof_rub_per_year_dict = \
                                profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop, prof_per_year_dict,
                                                   prof_rub_per_year_dict, i)
                            sold_volume_lef = sold_volume_lef - sold_volume_in_loop
                            index_to_del.append(i)
                        elif bought_amount_left > 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker, prof_per_year_dict, prof_rub_per_year_dict \
                                = profit_calculation(ticker, 1, sale_row_number, sold_volume_in_loop,
                                                     prof_per_year_dict, prof_rub_per_year_dict, i)
                            ticker.buy_volume_array[i] = ticker.buy_volume_array[i] - sold_volume_lef
                            stop = True
                            break
                        elif bought_amount_left == 0:
                            sold_volume_in_loop = sold_volume_lef
                            ticker, prof_per_year_dict, prof_rub_per_year_dict \
                                = profit_calculation(ticker, 2, sale_row_number, sold_volume_in_loop,
                                                     prof_per_year_dict, prof_rub_per_year_dict, i)
                            index_to_del.append(i)
                            ticker.buy_volume_array[i] = 0
                            stop = True
                            break
                ticker.buy_volume_array = ticker.buy_volume_array[len(index_to_del):]
                ticker.index_buy_deals = ticker.index_buy_deals[len(index_to_del):]
                index_to_del = []
    if ticker.outstanding_volumes != sum(ticker.buy_volume_array):
        print(f"количество оставшихся бумаг {ticker.ticker} и полученных в результате подсчета не совпадают")
        error_array.append(ticker.ticker)

    # print('закончил выполнение culc функции')
    return ticker, error_array, prof_per_year_dict, prof_rub_per_year_dict


# вычисление профита по каждой сделке в зависимости от остатка бумаг
def profit_calculation(ticker, option, sale_row_number, sold_volume, prof_per_year_dict, profit_rub_per_year_dict, i=0):
    sets = settings_for_sec.settings(ticker.broker)
    # print('начал выполнение profit_calculation функции')
    if ticker.broker in ['FRIDOM', 'SBER']:
        commission = sold_volume / ticker.total_buy * ticker.commission
        commission_rub = sold_volume / ticker.total_buy * ticker.commission * ticker.df['ROE'][sale_row_number]
    else:
        commission = sold_volume / ticker.total_buy * ticker.df['sum'][sale_row_number] * ticker.commission
        commission_rub = sold_volume / ticker.df['volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] * \
                         ticker.commission
    if option == 0:  # разница бумаг 0 или положительная
        prof_rub = ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][ticker.index_buy_deals[0]] * \
                   ticker.df['price'][ticker.index_buy_deals[0]] * ticker.bonds_mult - commission_rub
        prof_usd = ticker.df['sum'][sale_row_number] - \
                   sold_volume * ticker.df['price'][ticker.index_buy_deals[0]] * ticker.bonds_mult - commission

    elif option == 1:  # разница бумаг отрицательная, первая итерация
        buy_row_number = ticker.index_buy_deals[i]
        prof_rub = sold_volume / ticker.df['volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df['ROE'][buy_row_number] * ticker.df['price'][buy_row_number] *\
                   ticker.bonds_mult - commission_rub # * \ticker.bonds_mult
        prof_usd = sold_volume * ticker.df['price'][sale_row_number] - sold_volume * \
                   ticker.df['price'][buy_row_number] - commission #* ticker.bonds_mult

    elif option == 2:  # разница бумаг отрицательная, следующие  итерации
        prof_rub = sold_volume / ticker.df['volume'][sale_row_number] * ticker.df['RUB_sum'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['ROE'] * \
                   ticker.df.iloc[ticker.index_buy_deals[i]]['price'] * ticker.bonds_mult - commission_rub #* ticker.bonds_mult
        prof_usd = sold_volume * ticker.df['price'][sale_row_number] - \
                   sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['price'] - commission # * ticker.bonds_mult

    if ticker.currency in ['RUB', 'RUR']:
        prof_usd = prof_rub * ticker.exchange_to_usd
        ticker.prof_for_sold_securities += prof_usd
    else:
        ticker.prof_for_sold_securities += prof_usd * ticker.exchange_to_usd
    ticker.prof_for_sold_securities_rub += prof_rub

    row_to_fill = sale_row_number + i
    # проверка чтобы не было перезаписи вычислений в таблице каждой бумаги, чтобы проще делать проверку вычислений
    if ticker.filled_row >= row_to_fill:
        row_to_fill = ticker.filled_row + 1
        ticker.filled_row = row_to_fill
    if ticker.df.shape[0] == row_to_fill:
        new_row = {'profit_rus': prof_rub, 'prof_usd': prof_usd}
        ticker.df = ticker.df.append(new_row, ignore_index=True)
    else:
        ticker.df['profit_rus'][row_to_fill] = prof_rub
        ticker.df['prof_usd'][row_to_fill] = prof_usd
    ticker.filled_row = row_to_fill
    # print('закончил profit_calculation')
    # Заполнение прибыли по году
    prof_per_year_dict[str(ticker.df.iloc[:, sets['Дата']][sale_row_number].year)].append(round(prof_usd, 2))
    profit_rub_per_year_dict[str(ticker.df.iloc[:, sets['Дата']][sale_row_number].year)].append(round(prof_rub, 2))

    return ticker, prof_per_year_dict, profit_rub_per_year_dict


# подсчет прибыли по оставшимся бумагам. исходя из их средней цены и текущей цены
def outstanding_volume_price(ticker, error_array):
    # print('start outstanding_volume_price')
    sum_in_usd = 0
    sum_in_rub = 0
    if len(ticker.buy_volume_array) != 0:
        if ticker.current_price != 'N/A':
            for number, line in enumerate(ticker.index_buy_deals):
                sum_in_usd += ticker.buy_volume_array[number] * ticker.df['price'][line] * ticker.bonds_mult
                sum_in_rub += ticker.buy_volume_array[number] * ticker.df['price'][line] * ticker.bonds_mult \
                              * ticker.df['ROE'][line]
            ticker.average_roe_for_outstanding_volumes = round(sum_in_rub / sum_in_usd, 2)
            ticker.average_price_usd = \
                round(sum_in_rub / (ticker.average_roe_for_outstanding_volumes * sum(ticker.buy_volume_array)), 2)
            ticker.average_price_rub = round(sum_in_rub / sum(ticker.buy_volume_array), 2)
            try:
                ticker.profit_for_outstanding_volumes = round(((ticker.current_price - ticker.average_price_usd) *
                                                               ticker.outstanding_volumes * ticker.exchange_to_usd), 2)
                ticker.full_profit = round(ticker.prof_for_sold_securities + ticker.profit_for_outstanding_volumes, 2)
            except:
                ticker.profit_for_outstanding_volumes = 'N/A'
                ticker.full_profit = 'N/A'
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
        print(f"количество оставшихся бумаг {ticker.ticker} и полученных в результате подсчета не совпадают")
        error_array.append(ticker.ticker)

    return ticker, error_array
