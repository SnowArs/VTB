def profit_loss_calculation(df, number, corrected_profit, p_l_usd, p_l_for_percentage_usd):
    rub_sum = df['RUB_sum']
    if number == 0:
        prof_loss = df['RUB_sum'][index] - sale_volume * \
                    df['ROE'][index_arr[0]] * df['Price'][index_arr[0]]
        # corrected_profit = check_ndfl(prof_loss) + corrected_profit  # check NDFL
        prof_loss_usd = df['Sum'][index] - sale_volume * \
                        df['Price'][index_arr[0]] - \
                        check_ndfl(prof_loss)[1] / df['ROE'][index]
        p_l_for_percentage_usd = sale_volume * df['Price'][index_arr[0]] + \
                                 p_l_for_percentage_usd
    elif number == 1:
        prof_loss = (sale_volume + close) * df['ROE'][index] * \
                    df['Price'][index] - \
                    (sale_volume + close) * df['ROE'][buy_ind] * \
                    df['Price'][buy_ind]
        # corrected_profit = check_ndfl(prof_loss) + corrected_profit
        prof_loss_usd = (sale_volume + close) * df['Price'][index] - (sale_volume + close) \
                        * df['Price'][buy_ind] - \
                        check_ndfl(prof_loss)[1] / df['ROE'][index]
        p_l_for_percentage_usd = (sale_volume + close) * df['Price'][index_arr[0]] + \
                                 p_l_for_percentage_usd
    else:
        prof_loss = buy_arr[i] * df['ROE'][index] * df['Price'][index] - \
                    buy_arr[i] * df['ROE'][buy_ind] * df['Price'][
                        buy_ind]
        # corrected_profit = check_ndfl(prof_loss) + corrected_profit
        prof_loss_usd = buy_arr[i] * df['Price'][index] - buy_arr[i] * \
                        df['Price'][buy_ind] - \
                        check_ndfl(prof_loss)[1] / df['ROE'][index]
        p_l_for_percentage_usd = buy_arr[i] * df['Price'][index_arr[0]] + p_l_for_percentage_usd
    corrected_profit = check_ndfl(prof_loss) + corrected_profit
    p_l_usd = prof_loss_usd + p_l_usd
    #    print(round(prof_loss, 1), round(corrected_profit, 1), round(p_l_usd, 1), round(p_l_for_percentage_usd, 1))
    return corrected_profit, p_l_usd, p_l_for_percentage_usd