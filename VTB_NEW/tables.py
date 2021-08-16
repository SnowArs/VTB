RUS_TABLE_COLUMN = [ticker.name,
                     ticker.total_buy,
                     ticker.total_sell,
                     ticker.outstanding_volumes,
                     int(prof_loss_for_sold_securities_rus),
                     round(average_buy, 1),
                     current_price,
                     int(profit_for_outstanding_volumes_rus),
                     int(total_profit_rus)]