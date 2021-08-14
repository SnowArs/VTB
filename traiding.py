from tradingview_ta import TA_Handler, Interval, Exchange

tesla = TA_Handler(
    symbol="743",
    screener="hongkong",
    exchange="HKEX",
    interval=Interval.INTERVAL_1_DAY
)
print(tesla.get_analysis().indicators['close'])