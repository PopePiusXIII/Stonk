import numpy as np
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
from pprint import pprint
import time

Ticker = 'bac'
requests_headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
IEXTestToken = 'Tpk_9f4a350423954be3b70ec31a1b20102d'
IEXRealToken = 'pk_acd6e54847cd428b8959702163eca5ba'
Date = '2017-06-30'
DateStripped = Date.replace('-', '')

# CLOUD URL WILL CHARGE CREDITS TO ACCOUNT AND RETURN ACCURATE DATA - FOR FUNCTIONAL USE
IEXCloudUrl = 'https://cloud.iexapis.com/stable/stock/' + Ticker + '/chart/date/' + DateStripped + '?chartByDay=true&token=' + IEXRealToken

# SANDBOX URL IS FREE TO USE, HOWEVER, THE RETURNED DATA IS GARBLED - FOR TESTING ONLY
IEXSandboxUrl = 'https://sandbox.iexapis.com/stable/stock/' + Ticker + '/chart/date/' + DateStripped + '?chartByDay=true&token=' + IEXTestToken
print(IEXSandboxUrl)

#c = p.Client(api_token=IEXTestToken, version= 'sandbox')

# Processing using the IEX api costs 3 credits per search. Free token is capped at 500k tokens and does not replenish.
# Subscription begins at $9/month for 5 million credits/month, this would let us look at 15 years of data on 27.8k
# ticker searches. In free tier data only goes back 5 years. Much, much faster than the yf.download method
IEXStart = time.process_time()
response = requests.get(IEXSandboxUrl, headers = requests_headers)
data = response.json()
IEXStop = time.process_time()
print(data[0]['close'])
print(IEXStop - IEXStart)

# Yahoo finance is free but has been broken in the past and we are at the mercy of yahoo since the package is
# unaffliated with yahoo
YFStart = time.process_time()
Date2 = datetime.strptime(Date, '%Y-%m-%d').date() + timedelta(days= 1)
data2 = yf.download(Ticker, start = Date, end = Date2)
YFStop = time.process_time()
print(data2)
print(YFStop - YFStart)
