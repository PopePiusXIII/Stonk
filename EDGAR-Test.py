import numpy as np
import pandas as pd
import requests
from pprint import pprint
import json
from urllib.request import urlopen

#Pull the list of tickers from SEC site
TickerListDF = pd.read_csv('https://sec.gov/include/ticker.txt', sep = '\t', names= ['Ticker', 'CIK'], index_col= 'Ticker')

#User input ticker
Ticker = 'aapl'

#Finds corresponding CIK number for the ticker
TickerInfo = TickerListDF.loc[Ticker]
CIK = str(TickerInfo['CIK'])
CIK = CIK.zfill(10)

print('Ticker: ', Ticker.upper())
print('CIK #: ', CIK)

#EDGAR page for requested ticker
url = 'https://data.sec.gov/submissions/CIK' + CIK + '.json'

#Spoofs python browser as actual browser
requests_headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

#Get the data, do not remove headers
response = requests.get(url, headers= requests_headers)

#Whole next section is just HTTP response codes to debug
ConnectedSuccessfully = '200'
Redirected = '301'
BadRequest = '400'
NotAuthenticated = '401'
Forbidden = '403'
NotFound = '404'
ServerNotReady = '503'

response_status = str(response.status_code)

if ConnectedSuccessfully in response_status:
    print('Website Response = 200: Connected successfully')
elif Redirected in response_status:
    print('Website Response = 301: Redirected to a different endpoint')
elif BadRequest in response_status:
    print('Website Response = 400: Bad request, try again')
elif NotAuthenticated in response_status:
    print('Website Response = 401: Login required')
elif Forbidden in response_status:
    print('Website Response = 403: Forbidden')
elif NotFound in response_status:
    print('Website Response = 404: Cannot access requested site')
elif ServerNotReady in response_status:
    print('Website Response = 503: Server is not ready to handle request')
else:
    print('N/A')

#Output EDGAR data
EDGAR_json = response.json()
pprint(EDGAR_json)

data = pd.DataFrame.from_dict(EDGAR_json, orient='index')
print(data)
