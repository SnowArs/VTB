from moex import ndfl_func


def culc(ticker, ndfl, profit_in_usd):
    print('начал выполнение culc функции')
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['Volume'][sale_row_number]
        bought_volume = ticker.buy_volume_array[0]
        diff_volume = bought_volume - sold_volume
        while not stop:
            if diff_volume == 0:
                ndfl, profit_in_usd = profit_loss_calculation(ticker, 0, sale_row_number, sold_volume,
                                                              ndfl, profit_in_usd, diff_volume)
                # prof_loss_rur = ticker.df['RUB_sum'][sale_row_number] - \
                #                 sold_volume * ticker.df['ROE'][ticker.index_sell_deals[0]] * \
                #                 ticker.df['Price'][ticker.index_sell_deals[0]]
                # prof_loss_usd = ticker.df['Sum'][sale_row_number] - \
                #                 sold_volume * ticker.df['Price'][ticker.index_sell_deals[0]] - \
                #                 ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]
                # p_l_for_percentage_usd = sold_volume * ticker.df['Price'][ticker.index_sell_deals[0]] + \
                #                          p_l_for_percentage_usd
                ticker.buy_volume_array = ticker.buy_volume_array[1:]
                ticker.index_buy_deals = ticker.index_buy_deals[1:]
                break
            elif diff_volume > 0:
                ndfl, profit_in_usd = profit_loss_calculation(ticker, 0, sale_row_number, sold_volume,
                                                              ndfl, profit_in_usd, diff_volume)
                ticker.buy_volume_array[0] = ticker.buy_volume_array[0] - sold_volume
                break
            else:  # отрицательный объем
                for i, buy_ind in enumerate(ticker.index_buy_deals):
                    if i == 0:
                        ndfl, profit_in_usd = profit_loss_calculation(ticker, 1, sale_row_number, sold_volume,
                                                                      ndfl, profit_in_usd, diff_volume, i)
                        negative_amount = diff_volume
                        ticker.buy_volume_array[0] = 0
                        index_to_del.append(i)
                    else:
                        diff = ticker.buy_volume_array[i] + negative_amount
                        ndfl, profit_in_usd = profit_loss_calculation(ticker, 2, sale_row_number, -negative_amount,
                                                                      ndfl, profit_in_usd, diff_volume, i)
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
    return ndfl, profit_in_usd


def profit_loss_calculation(ticker, option, sale_row_number, sold_volume, ndfl_, p_l_usd, diff_volume, i=0):
    if option == 0:
        prof_loss_rur = ticker.df['RUB_sum'][sale_row_number] - \
                        sold_volume * ticker.df['ROE'][ticker.index_buy_deals[0]] * \
                        ticker.df['Price'][ticker.index_buy_deals[0]]
        prof_loss_usd = ticker.df['Sum'][sale_row_number] - \
                        sold_volume * ticker.df['Price'][ticker.index_buy_deals[0]] - \
                        ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]

    elif option == 1:
        prof_loss_rur = (sold_volume + diff_volume)/sold_volume * ticker.df['RUB_sum'][sale_row_number] - \
                        (sold_volume + diff_volume) * ticker.df['ROE'][i] * ticker.df['Price'][i]
        prof_loss_usd = (sold_volume + diff_volume) * ticker.df['Price'][sale_row_number] - (sold_volume + diff_volume) \
                        * ticker.df['Price'][i] - ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]

    else:
        prof_loss_rur = sold_volume * ticker.df['ROE'][sale_row_number] * ticker.df['Price'][sale_row_number] - \
                        sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['ROE'] *\
                        ticker.df.iloc[ticker.index_buy_deals[i]]['Price']
        prof_loss_usd = sold_volume * ticker.df['Price'][sale_row_number] -\
                        sold_volume * ticker.df.iloc[ticker.index_buy_deals[i]]['Price'] - \
                        ndfl_func(prof_loss_rur) / ticker.df['ROE'][sale_row_number]
        
    ndfl_ = ndfl_func(prof_loss_rur) + ndfl_
    p_l_usd = prof_loss_usd + p_l_usd
    #    print(round(prof_loss_rur, 1), round(ndfl_, 1), round(p_l_usd, 1), round(p_l_for_percentage_usd, 1))
    return ndfl_, p_l_usd
