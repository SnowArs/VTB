
RUS_TABLE_COLUMN = ['ticker.name',
                    'ticker.total_buy',
                    'ticker.total_sell',
                    'ticker.outstanding_volumes',
                    'int(prof_loss_for_sold_securities_rus)',
                    'round(average_buy, 1)',
                    'current_price',
                    'int(profit_for_outstanding_volumes_rus)',
                    'int(total_profit_rus)']

NON_RUS_TABLE_COLUMNS =[ticker.name,
                        ticker.total_buy,
                        ticker.total_sell,
                        ticker.outstanding_volumes,
                        int(ticker.ndfl_full),
                        int(ticker.profit_in_usd * ticker.exchange_to_usd),
                        round(ticker.average_price_usd, 1),
                        round(ticker.current_price, 1),
                        round(ticker.profit_for_outstanding_volumes * ticker.exchange_to_usd, 1),
                        int(ticker.total_profit * ticker.exchange_to_usd)]

if __name__ == '__main__':
    pass