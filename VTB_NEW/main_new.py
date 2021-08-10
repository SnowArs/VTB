import warnings
from prettytable import PrettyTable
from prettytable import ALL
from moex import *
import class_new
import os.path

warnings.filterwarnings('ignore')


def profit_loss_calculation(list_):
    df_ = list_[0]
    option_ = list_[1]
    ndfl_ = list_[2]
    p_l_usd = list_[3]
    p_l_for_percentage_usd = list_[4]

    if option_ == 0:
        prof_loss_rur = df_['RUB_sum'][index] - sale_volume * df_['ROE'][index_arr[0]] * df_['Price'][index_arr[0]]
        prof_loss_usd = df_['Sum'][index] - sale_volume * df_['Price'][index_arr[0]] - \
                        ndfl_func(prof_loss_rur) / df_['ROE'][index]
        p_l_for_percentage_usd = sale_volume * df_['Price'][index_arr[0]] + p_l_for_percentage_usd
    elif option_ == 1:
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


df = pd.read_excel('сделки_ВТБ.xls', sheet_name='DealOwnsReport', header=3)
df = df.loc[df['Тип сделки'] == 'Клиентская'].reset_index(drop=True)
full_list_of_securities = df['Код инструмента'].unique().tolist()

# группировка
df = df.groupby(['Дата вал.', 'Код инструмента', 'B/S', 'Валюта']).agg(
    Price=pd.NamedAgg(column='Цена', aggfunc='mean'),
    Volume=pd.NamedAgg(column='Кол-во', aggfunc='sum'),
    NKD=pd.NamedAgg(column='НКД', aggfunc='sum'),
    Sum=pd.NamedAgg(column='Объем', aggfunc='sum')
)

df.reset_index(drop=False, inplace=True)
# создание двух новых колонок с заполнением
df = pd.concat([df, pd.DataFrame(columns=['ROE_index'])])
for index, row in df.iterrows():
    df['ROE_index'][index] = row['Дата вал.'].strftime('%Y-%m-%d') + '_' + row['Валюта']

# заполнение ROE/RUB_sum
if os.path.exists('roe_table.csv'):
    df_roe = pd.read_csv('roe_table.csv', usecols=['ROE_index', 'ROE'])
    # df_roe['Дата вал.'] = df_roe['Дата вал.'].apply(pd.Timestamp)
    df = df.merge(df_roe, how='left', left_on='ROE_index', right_on='ROE_index')
    df.loc[df['Валюта'] == 'RUR', 'ROE'] = 1
    # df_with_missed_roe
    if df.loc[df['ROE'].isna()].empty:
        print('ROE по всем датам проставленно')
    else:
        for index, row in df.loc[df['ROE'].isna()].iterrows():
            df['ROE'][index] = fill_roe(row['Дата вал.'], row['Валюта'], df['Дата вал.'].min())

else:
    for index, row in df.iterrows():
        df = pd.concat([df, pd.DataFrame(columns=['ROE'])])
        df['ROE'][index] = fill_roe(row['Дата вал.'], row['Валюта'], df['Дата вал.'].min())
df_roe = df.loc[(df['ROE'] != 1) & (df['Дата вал.'] < dt.datetime.today().strftime('%Y-%m-%d')), ['ROE_index', 'ROE']]
df_roe = df_roe.drop_duplicates('ROE_index', ignore_index=True)
df_roe.to_csv('roe_table.csv', index=False)

df['RUB_sum'] = df['Sum'] * df['ROE']
df = df.astype({'ROE': 'float', 'RUB_sum': 'float'})

full_ndfl = 0
full_prof_loss_usd = 0
full_profit_loss_percentage = 0
Full_potential_profit = 0
Full_potential_profit_rus = 0

# сознадние таблицы вывода
mytable = PrettyTable()
# mytable.hrules = ALL
mytable_rus = PrettyTable()
mytable_rus.hrules = ALL
# имена полей таблицы
field_names = ['Тикер', 'Куплено', 'Продано', 'Остаток', 'НДФЛ, РУБ', 'Прибыль в USD', 'Прибыль в usd в %',
               'средняя цена', 'текущая цена', 'потенциальная прибыль', 'прибыль всех бумаг']
mytable.field_names = field_names
mytable_rus.field_names = field_names[0:4] + ['заф прибыль РУБ'] + field_names[7:]

for security in full_list_of_securities:
    df_for_particular_security = df.loc[df['Код инструмента'] == security].reset_index(drop=True)
    ticker = class_new.Ticker(df_for_particular_security)
    prof_loss_for_sold_securities = 0
    buy_arr = []
    index_arr = []
    index_to_del = []
    ndfl = 0
    prof_loss_usd = 0
    profit_in_usd = 0
    profit_for_percentage_calculation_usd = 0
    total_profit_rus = 0
    total_profit = 0
    # указание на ошибку если остаток акций отрицательный
    if ticker.outstanding_volumes < 0:
        print(f'похоже в позиции {ticker.name} проблемы с вычислениями, так как остаток отрицательный')
        continue
    # обработка рублевых бумаг
    if ticker.currency == 'RUR':
        prof_loss_for_sold_securities_rus, average_buy, profit_for_outstanding_volumes_rus, total_profit_rus = \
            class_new.Calculations.rub_securities_processing(ticker, df_for_particular_security)
        mytable_rus.add_row([ticker.name,
                             ticker.total_buy,
                             ticker.total_sell,
                             ticker.outstanding_volumes,
                             int(prof_loss_for_sold_securities_rus),
                             round(average_buy, 1),
                             current_price,
                             int(profit_for_outstanding_volumes_rus),
                             int(total_profit_rus)])

    # блок вычисления прибыли и убытков по бумаге в USD и EUR
    else:
        for index, deal in df_for_particular_security.iterrows():
            if deal['B/S'] == 'Покупка':
                buy_arr.append(deal['Volume'])
                index_arr.append(index)
            else:
                sale_volume = deal['Volume']
                buy_volume = buy_arr[0]
                close = buy_volume - sale_volume
                option = 0
                list_for_prof_los_func = [df_for_particular_security, option, ndfl, profit_in_usd,
                                                  profit_for_percentage_calculation_usd]
                if close == 0:
                    ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                        = profit_loss_calculation(list_for_prof_los_func)
                    buy_arr.pop(0)
                    index_arr.pop(0)

                elif close > 0:
                    ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                        = profit_loss_calculation(list_for_prof_los_func)
                    buy_arr[0] = buy_arr[0] - sale_volume
                else:
                    for i, buy_ind in enumerate(index_arr):
                        if i == 0:
                            option = 1
                            ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                                = profit_loss_calculation(list_for_prof_los_func)
                            close_diff = close
                            index_to_del.append(i)
                        else:
                            diff = buy_arr[i] + close_diff
                            option = 2
                            ndfl, profit_in_usd, profit_for_percentage_calculation_usd \
                                = profit_loss_calculation(list_for_prof_los_func)
                            if diff < 0:
                                close_diff = diff
                                index_to_del.append(i)
                            elif diff > 0:
                                buy_arr[i] = buy_arr[i] - diff
                                break
                            else:
                                index_to_del.append(i)
                                break
                    buy_arr = buy_arr[len(index_to_del):]
                    index_arr = index_arr[len(index_to_del):]

        # вычисление средней цены  оставшихся бумаг в рублях и валюте
        sum_in_usd = 0
        sum_in_rub = 0
        if len(buy_arr) != 0:
            for number, line in enumerate(index_arr):
                sum_in_usd = buy_arr[number] * df_for_particular_security['Price'][line] + sum_in_usd
                sum_in_rub = buy_arr[number] * df_for_particular_security['Price'][line] * \
                             df_for_particular_security['ROE'][line] + sum_in_rub
            average_price_usd = sum_in_usd / sum(buy_arr)
            average_price_rub = sum_in_rub / sum(buy_arr)

            try:
                profit_for_outstanding_volumes = (get_current_price(ticker.name) - average_price_usd) \
                                                 * ticker.outstanding_volumes
                total_profit = int(profit_in_usd + profit_for_outstanding_volumes -\
                                   ndfl_func(profit_for_outstanding_volumes))
                current_price = round(get_current_price(ticker.name), 1)
            except IndexError:
                profit_for_outstanding_volumes = 'N/A'
                total_profit = 'N/A'
                current_price = 'N/A'

        else:
            average_price_usd = 0
            profit_for_outstanding_volumes = 0
            average_price_rub = 0
            total_profit = int(profit_in_usd)
            current_price = 0

        if profit_for_percentage_calculation_usd != 0:
            p_l_for_percentage_calc = round(profit_in_usd / profit_for_percentage_calculation_usd * 100, 1)
        else:
            p_l_for_percentage_calc = round(profit_in_usd / 1 * 100, 1)

        mytable.add_row([ticker.name,
                         ticker.total_buy,
                         ticker.total_sell,
                         ticker.outstanding_volumes,
                         int(ndfl),
                         int(profit_in_usd),
                         p_l_for_percentage_calc,
                         round(average_price_usd, 1),
                         current_price,
                         round(profit_for_outstanding_volumes, 1),
                         int(total_profit)])

    full_ndfl = full_ndfl + ndfl
    full_prof_loss_usd = full_prof_loss_usd + profit_in_usd
    full_profit_loss_percentage = full_profit_loss_percentage + profit_for_percentage_calculation_usd
    Full_potential_profit = Full_potential_profit + total_profit
    Full_potential_profit_rus = Full_potential_profit_rus + total_profit_rus
print()
print(mytable_rus)
print(f'по рублевым бумагам прибыль: {int(Full_potential_profit_rus)}')
print()
print(mytable)
print(f'НДФЛ по всем бумагам в РУБ:  {int(full_ndfl)},\
        общая прибыль по всем бумагам в USD: {int(Full_potential_profit)},\
         общая прибыль в % {round(full_prof_loss_usd / full_profit_loss_percentage * 100, 1)} ')
