import yfinance as yf

msft = yf.Ticker("MSFT")


def price_to_sales(mkt_cap, revenue):
    return mkt_cap / revenue


def price_to_earings(mkt_cap, earnings):
    return mkt_cap / earnings

def historical_price_to_earnings(object):
    for