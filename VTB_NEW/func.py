from moex import ndfl_func


def culc(ticker, ndfl, profit_in_usd, profit_for_percentage_calculation_usd):
    index_to_del = []
    for sale_row_number in ticker.index_sell_deals:
        stop = False
        sold_volume = ticker.df['Volume'][sale_row_number]
        bought_volume = ticker.buy_volume_array[0]
        diff_volume = bought_volume - sold_volume
        for index in range(0, sale_row_number):
            if stop:
                break
            else:
                if diff_volume == 0:
                    ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                        = profit_loss_calculation(ticker.df, 0, ndfl, profit_in_usd,
                                                  profit_for_percentage_calculation_usd)
                    ticker.buy_volume_array = ticker.buy_volume_array[1:]
                    ticker.index_buy_deals = ticker.index_buy_deals[1:]
                    break
                elif diff_volume > 0:
                    # ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                    #     = profit_loss_calculation(df_for_particular_security, 0, ndfl, profit_in_usd,
                    #                               profit_for_percentage_calculation_usd)
                    ticker.buy_volume_array[0] = ticker.buy_volume_array[index] - sold_volume
                    break
                else:
                    for i, buy_ind in enumerate(ticker.index_buy_deals):
                        if i == 0:
                            # ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                            #     = profit_loss_calculation(df_for_particular_security, 1, ndfl, profit_in_usd,
                            #                               profit_for_percentage_calculation_usd)
                            negative_amount = diff_volume
                            ticker.buy_volume_array[i] = 0
                            index_to_del.append(i)
                        else:
                            diff = ticker.buy_volume_array[i] + negative_amount
                            # ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                            #     = profit_loss_calculation(df_for_particular_security, 2, ndfl, profit_in_usd,
                            #                               profit_for_percentage_calculation_usd)
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

    return ticker.buy_volume_array, ticker.index_buy_deals



def profit_loss_calculation(df_, option, ndfl_, p_l_usd, p_l_for_percentage_usd, index, sale_volume, index_arr,
                            close, buy_ind, buy_arr, i):
    if option == 0:
        prof_loss_rur = df_['RUB_sum'][index] - sale_volume * df_['ROE'][index_arr[0]] * df_['Price'][index_arr[0]]
        prof_loss_usd = df_['Sum'][index] - sale_volume * df_['Price'][index_arr[0]] - \
                        ndfl_func(prof_loss_rur) / df_['ROE'][index]
        p_l_for_percentage_usd = sale_volume * df_['Price'][index_arr[0]] + p_l_for_percentage_usd
    elif option == 1:
        prof_loss_rur = (sale_volume + close) * df_['ROE'][index] * df_['Price'][index] - \
                        (sale_volume + close) * df_['ROE'][buy_ind] * df_['Price'][buy_ind]
        prof_loss_usd = (sale_volume + close) * df_['Price'][index] - (sale_volume + close) \
                        * df_['Price'][buy_ind] - ndfl_func(prof_loss_rur) / df_['ROE'][index]
        p_l_for_percentage_usd = (sale_volume + close) * df_['Price'][index_arr[0]] + p_l_for_percentage_usd
    else:
        prof_loss_rur = buy_arr[i] * df_['ROE'][index] * df_['Price'][index] - \
                        buy_arr[i] * df_['ROE'][buy_ind] * df_['Price'][buy_ind]
        prof_loss_usd = buy_arr[i] * df_['Price'][index] - buy_arr[i] * df_['Price'][buy_ind] - \
                        ndfl_func(prof_loss_rur) / df_['ROE'][index]
        p_l_for_percentage_usd = buy_arr[i] * df_['Price'][index_arr[0]] + p_l_for_percentage_usd
    ndfl_ = ndfl_func(prof_loss_rur) + ndfl_
    p_l_usd = prof_loss_usd + p_l_usd
    #    print(round(prof_loss_rur, 1), round(ndfl_, 1), round(p_l_usd, 1), round(p_l_for_percentage_usd, 1))
    return ndfl_, p_l_usd, p_l_for_percentage_usd