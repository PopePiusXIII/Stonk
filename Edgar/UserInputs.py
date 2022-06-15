from Functions import *

# User input ticker
Ticker = 'aapl'  # spacs is where iex suffers, need to find out if there's a workaround

# Values to lookup within the json result, will look up all values in list and will return them as one dataframe column.
# For example, you will not be able to create a dataframe with revenue and net profit in separate columns
# THE ORDER OF THIS LIST MATTERS, SORT FROM MOST TO LEAST IMPORTANT
LookUpValueList = [RevenueList, NetIncomeList, EPSList, SharesOutstandingList, EBITList, DepreciationAndAmortization]

# IEX Cloud Inputs:
CloudOrSandbox = 'Sandbox'  # <-- Input Cloud for real data or Sandbox   for testing purposes, sandbox is inaccurate
YearsBack = 5  # <-- On the free tier for now, 15 years when on paid tier

# ISO 8601 date format
ISO8601 = '%Y-%m-%d'

# Spoofs as real browser
requests_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}