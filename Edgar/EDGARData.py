from datetime import datetime, timedelta, date
import time
import os
import numpy as np
import pandas as pd
import requests
from pprint import pprint
from itertools import chain
from bs4 import BeautifulSoup as bs
from functools import reduce
from UserInputs import *
from Functions import *

"""
The SEC requires all companies to submit their quarterly and annual reports (10-Q and 10-K) using a 'standard' taxonomy 
in a xml/xbrl format. Because there is a standardized taxonomy, the SEC put together a browser API that spits out data 
using only the company CIK number and the taxonomy code you are interested in. More information can be found here:
https://www.sec.gov/edgar/sec-api-documentation
"""

StartOverallTimer = time.perf_counter()

# This section initializes user inputs and constants
Timer1 = 'User Inputs and Constants Timer:'
StartTimer1 = time.perf_counter()
DeltaDate, TickerListDF, BaseUrlIEX, IEXToken, IEXRate, CIKLeadingZeros = initialize(YearsBack, CloudOrSandbox, Ticker)
StopTimer1 = time.perf_counter()

Timer2 = 'Scrape EDGAR Filing Data and Populate DataFrame Timer:'
StartTimer2 = time.perf_counter()
FilingResultsDFList = []
for k in range(0, len(LookUpValueList)):
    LookUpValue = LookUpValueList[k]
    # This sections finds the valid filing taxonomy and pulls the json data from the SEC API
    ValidTaxonomy, EDGAR_json, EDGAR_DEI_json, response, url = sec_api_response(CIKLeadingZeros, requests_headers)
    print(LookUpValue[0], "", end='')
    general_http_response_codes(response)

    # This sections cleans up and populates dataframe
    LookUpValueExists = lookup_value_exists(LookUpValue, ValidTaxonomy)
    FormResults, EndDateResults, ValResults, QorKResults, ValLookedUpResults = get_requested_data(LookUpValueExists, EDGAR_json, EDGAR_DEI_json, LookUpValue, DeltaDate, ISO8601)
    FilingResultsDF = data_to_dataframe(FormResults, EndDateResults, ValResults, QorKResults, ValLookedUpResults, LookUpValue)
    FilingResultsDF = remove_inferior_rows(LookUpValue, FilingResultsDF)
    FilingResultsDFList += [FilingResultsDF]
print(url)
StopTimer2 = time.perf_counter()

Timer3 = 'Calculate Quarterly Value Timer:'
StartTimer3 = time.perf_counter()
FilingResultsDFListCleanedUp = []
DataFrameLengths = []
for k in range(0, len(FilingResultsDFList)):
    # This sections cleans up dataframe further and returns calculated values if quarterly isn't reported in 10-K
    FilingResultsDF = FilingResultsDFList[k]
    FilingResultsDF = select_quarterly_over_annual(FilingResultsDF)
    FilingResultsDF = calculate_quarterly(k, FilingResultsDF, ISO8601, LookUpValueList)
    # Drop columns used for troubleshooting
    FilingResultsDF = pd.DataFrame.drop(FilingResultsDF, columns= ['Form', 'Q or K', 'Lookup Val'])
    FilingResultsDFListCleanedUp += [FilingResultsDF]
    DataFrameLengths += [len(FilingResultsDF)]
StopTimer3 = time.perf_counter()

# This random lambda function merges filing data frames along the date column regardless of how many dataframes there
# are since pd.merge is limited to two dataframes
Timer4 = 'Merge Filing Data DataFrames:'
StartTimer4 = time.perf_counter()
FilingResultsDF = reduce(lambda left, right: pd.merge(left, right, on=['End Date'], how='left'), FilingResultsDFListCleanedUp)
StopTimer4 = time.perf_counter()

# This section finds a valid date for a historic quote
Timer5 = 'Find Valid Market Date Timer:'
StartTimer5 = time.perf_counter()
ValidEndDateList = historic_quote_date(FilingResultsDF, ISO8601)
StopTimer5 = time.perf_counter()

# This section finds the historic quote
Timer6 = 'IEX Historic Quote Timer:'
StartTimer6 = time.perf_counter()
HistoricQuoteDateList, HistoricQuoteList = historic_quote(ValidEndDateList, ISO8601, requests_headers, BaseUrlIEX, Ticker, IEXToken, IEXRate)
StopTimer6 = time.perf_counter()

# This section merges the filing dataframe and the historic quote dataframe if they are the same length
Timer7 = 'Merge DataFrames Timer:'
StartTimer7 = time.perf_counter()
ConcatDataFrame = merge_dataframes(HistoricQuoteList, HistoricQuoteDateList, FilingResultsDF)
StopTimer7 = time.perf_counter()

# This section calculates the PE ratio
Timer8 = 'Calculate PE Ratio Timer:'
StartTimer8 = time.perf_counter()
try:
    pe_ratio(ConcatDataFrame)
except:
    print(ConcatDataFrame)
StopTimer8 = time.perf_counter()

StopOverallTimer = time.perf_counter()

print(Timer1, (StopTimer1-StartTimer1), 'sec')
print(Timer2, (StopTimer2-StartTimer2), 'sec')
print(Timer3, (StopTimer3-StartTimer3), 'sec')
print(Timer4, (StopTimer4-StartTimer4), 'sec')
print(Timer5, (StopTimer5-StartTimer5), 'sec')
print(Timer6, (StopTimer6-StartTimer6), 'sec')
print(Timer7, (StopTimer7-StartTimer7), 'sec')
print(Timer8, (StopTimer8-StartTimer8), 'sec')
print('Overall Process Timer:', StopOverallTimer-StartOverallTimer, 'sec')

# Need to consider appropriate behavior if there are not 3 prior quarterly results to the annual result
