from datetime import datetime, timedelta, date
import time
import os
import numpy as np
import pandas as pd
import requests
from pprint import pprint
from itertools import chain
from bs4 import BeautifulSoup as bs
from FunctionsAndConstants import *

"""
The SEC requires all companies to submit their quarterly and annual reports (10-Q and 10-K) using a 'standard' taxonomy 
in a xml/xbrl format. Because there is a standardized taxonomy, the SEC put together a browser API that spits out data 
using only the company CIK number and the taxonomy code you are interested in. More information can be found here:
https://www.sec.gov/edgar/sec-api-documentation
"""

StartTimer1 = time.perf_counter()

# User input ticker
Ticker = 'gme'  # spacs is where iex suffers, need to find out if there's a workaround

# Values to lookup within the json result, will look up all values in list and will return them as one dataframe column.
# For example, you will not be able to create a dataframe with revenue and net profit in separate columns
# THE ORDER OF THIS LIST MATTERS, SORT FROM MOST TO LEAST IMPORTANT
LookUpValue = EPSList

# IEX Cloud Inputs:
CloudOrSandbox = 'Sandbox'  # <-- Input Cloud for real data or Sandbox for testing purposes, sandbox is inaccurate
YearsBack = 5  # <-- On the free tier for now, 15 years when on paid tier

# ISO 8601 date format
ISO8601 = '%Y-%m-%d'

# Show all rows and columns for dataframe
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Print current date and time, and calculate now minus 5 years + 1 day
print(datetime.now())
DeltaDate = datetime.now().date() - timedelta(days=((365*YearsBack)+1))

# Try statement to pull ticker list, tries for sec site but if it's down pulls locally
try:
    TickerListDF = pd.read_csv('https://sec.gov/include/ticker.txt', sep='\t', names=['Ticker', 'CIK'],
                               index_col='Ticker')
except:
    TickerListDF = pd.read_csv(r'C:/Users/modyv//Documents/GitHub/Stonk/ticker.txt', sep='\t',
                               names=['Ticker', 'CIK'], index_col='Ticker')

# Selects the appropriate response based off IEX version requested
if ('Cloud' in CloudOrSandbox) or ('cloud' in CloudOrSandbox):
    BaseUrlIEX = 'https://cloud.iexapis.com/stable/stock/'
    IEXToken = 'pk_acd6e54847cd428b8959702163eca5ba'
    IEXRate = 0.01
elif ('Sandbox' in CloudOrSandbox) or ('sandbox' in CloudOrSandbox):
    BaseUrlIEX = 'https://sandbox.iexapis.com/stable/stock/'
    IEXToken = 'Tpk_9f4a350423954be3b70ec31a1b20102d'
    IEXRate = 0.5
else:
    print('Input valid mode for IEX')
    exit()

StopTimer1 = time.perf_counter()

StartTimer2 = time.perf_counter()

# Finds corresponding CIK number for the ticker
TickerInfo = TickerListDF.loc[Ticker.lower()]
CIK = str(TickerInfo['CIK'])
CIKLeadingZeros = CIK.zfill(10)

print('Ticker: ', Ticker.upper())
print('CIK #: ', CIK)

# Spoofs as real browser
requests_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

# SEC filing api
url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + CIKLeadingZeros + '.json'
response = requests.get(url, headers= requests_headers)

# Returns the response code of the site
general_http_response_codes(response)

# Tries US-GAAP and IFRS-Full taxonomies and makes a list of all the tags in the correct taxonomy
# American companies *should* be using US-GAAP, international companies *should* be using IFRS-Full
USGAAPList = []
IFRSFullList = []
try:
    # Output EDGAR data
    EDGAR_json = response.json()
    EDGAR_json = EDGAR_json['facts']['us-gaap']
    JSONKEYS = EDGAR_json.keys()
    List = list(JSONKEYS)
    USGAAPList += [List]
except:
    # Output EDGAR data
    EDGAR_json = response.json()
    EDGAR_json = EDGAR_json['facts']['ifrs-full']
    JSONKEYS = EDGAR_json.keys()
    List = list(JSONKEYS)
    IFRSFullList += [List]

# Decides what the valid taxonomy is for the given ticker
if USGAAPList:
    ValidTaxonomy = USGAAPList
elif IFRSFullList:
    ValidTaxonomy = IFRSFullList
else:
    print('No valid taxonomy')
    exit()

StopTimer2 = time.perf_counter()

StartTimer3 = time.perf_counter()

# Create a list to see if our LookUpValue exists. Since there are 13k+ companies with files dating back to who knows
# when it is best to pass multiple lookup values, however, if the lookup value doesn't exist then the code kicks back
# an error. Creating a list called 'LookUpValueExists' allows us to screen the given value before searching
LookUpValueExists = []
for i in range(0, len(LookUpValue)):
    if LookUpValue[i] in ValidTaxonomy[0]:
        LookUpValueExists += [i]
    else:
        LookUpValueExists += [-1]

# Return the form, the end date, the value, and identify if it is a quarterly or annual result
FormResults = []
EndDateResults = []
ValResults = []
QorKResults = []
ValLookedUpResults = []
for i in range(0, len(LookUpValueExists)):
    if LookUpValueExists[i] >= 0:
        LookUp = EDGAR_json[LookUpValue[i]]['units']
        # Automatically find the next json key
        Key = list(LookUp.keys())[0]
        LookUp = LookUp[Key]
        # Returns how many data points we are pulling for the given LookUpValue
        LookUpCount = len(LookUp)
        LookUpFormList = []
        LookUpEndDateList = []
        LookUpValList = []
        QorKColumn = []
        ValLookedUpList = []
        # Using the for loop below to screen the 'frame' json key. This frame key is used to identify whether the data
        # returned is quarterly annual within an annual filings. We also populate our dataframe 'Quarterly or Annual'
        # column using the frame data
        for j in range(0, LookUpCount):
            if 'frame' in LookUp[j]:
                Frame = LookUp[j]['frame']
                Form = LookUp[j]['form']
                EndDate = LookUp[j]['end']
                Val = LookUp[j]['val']
                ValLookedUp = [LookUpValueExists[i]]
                if (('Q' in Frame) or ('q' in Frame)) and (datetime.strptime(EndDate, ISO8601).date() >= DeltaDate):
                    QorKColumn += ['Q']
                    LookUpFormList += [Form]
                    LookUpEndDateList += [EndDate]
                    LookUpValList += [Val]
                    ValLookedUpList += [ValLookedUp]
                elif (('Q' not in Frame) or ('q' not in Frame)) and (datetime.strptime(EndDate, ISO8601).date() >= DeltaDate):
                    QorKColumn += ['K']
                    LookUpFormList += [Form]
                    LookUpEndDateList += [EndDate]
                    LookUpValList += [Val]
                    ValLookedUpList += [ValLookedUp]
        FormResults += [LookUpFormList]
        EndDateResults += [LookUpEndDateList]
        ValResults += [LookUpValList]
        QorKResults += [QorKColumn]
        ValLookedUpResults += [ValLookedUpList]

# Compile output into numpy array prior to dataframe creation
FormResults = list(chain.from_iterable(FormResults))
EndDateResults = list(chain.from_iterable(EndDateResults))
ValResults = list(chain.from_iterable(ValResults))
QorKResults = list(chain.from_iterable(QorKResults))
ValLookedUpResults = list(chain.from_iterable(ValLookedUpResults))

TotalLookUpCount = len(ValResults)
FormResultsArray = np.array(FormResults).reshape(TotalLookUpCount, 1)
EndDateResultsArray = np.array(EndDateResults).reshape(TotalLookUpCount, 1)
ValResultsArray = np.array(ValResults).reshape(TotalLookUpCount, 1)
QorKResultsArray = np.array(QorKResults).reshape(TotalLookUpCount, 1)
ValLookedUpArray = np.array(ValLookedUpResults).reshape(TotalLookUpCount, 1)

FilingResultsArray = np.concatenate((FormResultsArray,
                                     EndDateResultsArray, ValResultsArray,
                                     QorKResultsArray,
                                     ValLookedUpArray), axis=1)
FilingResultsDF = pd.DataFrame(FilingResultsArray, columns=['Form', 'End Date', LookUpValue[0], 'Q or K', 'Lookup Val'])

# Dataframe must be double sorted for next step to work properly
FilingResultsDF.sort_values(by=['End Date', 'Q or K'], inplace=True)
FilingResultsDF.reset_index(drop=True, inplace=True)

# Goes through FilingResultsDF and checks to see if multiple data points for the same date and the same 'Q or K' value.
# First for loop makes sure j+1 value does not fall outside the dataframe
# The inferior value (based off the user defined LookUpValue list order) is deleted
InferiorLookupValIndex = []
for i in range(1, (len(LookUpValue)+1)):
    for j in range(0, (len(FilingResultsDF)-i)):
        if ((FilingResultsDF.iloc[j+i, 4] > FilingResultsDF.iloc[j, 4]) and
                (FilingResultsDF.iloc[j+i, 1] == FilingResultsDF.iloc[j, 1]) and
                (FilingResultsDF.iloc[j+i, 3] == FilingResultsDF.iloc[j, 3])):
            InferiorLookupValIndex += [j+i]
        elif ((FilingResultsDF.iloc[j+i, 4] < FilingResultsDF.iloc[j, 4]) and
                (FilingResultsDF.iloc[j+i, 1] == FilingResultsDF.iloc[j, 1]) and
                (FilingResultsDF.iloc[j+i, 3] == FilingResultsDF.iloc[j, 3])):
            InferiorLookupValIndex += [j]

FilingResultsDF.drop(InferiorLookupValIndex, inplace=True)
FilingResultsDF.reset_index(drop=True, inplace=True)

StopTimer3 = time.perf_counter()

StartTimer4 = time.perf_counter()

# Identify duplicate End Dates
EndDateList = FilingResultsDF.loc[:, 'End Date']
EndDateList = EndDateList.values
# Returns the values of only the duplicates
UniqueEndDates, EndDateCount = np.unique(EndDateList, return_counts=True)
DuplicateEndDates = UniqueEndDates[EndDateCount > 1]

# Identifies the duplicate end dates index values
DuplicateDatesIndices = []
for i in range(0, len(DuplicateEndDates)):
    Duplicates = FilingResultsDF[FilingResultsDF['End Date'] == DuplicateEndDates[i]].index.values
    Duplicates = Duplicates.tolist()
    DuplicateDatesIndices += Duplicates

# Loops through dataframe to identify entries with identical dates with a Q and K val in the 'Q or K' column
RowsToDelete = []
for i in range(0, len(DuplicateDatesIndices)):
    RepetitiveDatesCheckVal1 = DuplicateDatesIndices[i]
    for j in range(0, len(DuplicateDatesIndices)):
        RepetitiveDatesCheckVal2 = DuplicateDatesIndices[j]
        if i != j:
            if (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 1]) \
                    and ((FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 3] == 'Q') and
                         (FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 3] == 'K')):
                RowsToDelete += [RepetitiveDatesCheckVal2]
            elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 1]) \
                    and ((FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 3] == 'K') and
                         (FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 3] == 'Q')):
                RowsToDelete += [RepetitiveDatesCheckVal1]
            elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 1]) \
                    and (('Q' in FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 0]) and
                         ('K' in FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 0])):
                RowsToDelete += [RepetitiveDatesCheckVal2]
            elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 1]) \
                    and (('K' in FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 0]) and
                         ('Q' in FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 0])):
                RowsToDelete += [RepetitiveDatesCheckVal1]

# Deletes previously identified rows
UniqueRowsToDelete = np.unique(RowsToDelete)
UniqueRowsToDelete = UniqueRowsToDelete.tolist()
FilingResultsDF.drop(RowsToDelete, inplace=True)

# Remove duplicate rows if they've managed to pass through and reset the dataframe index
FilingResultsDF.drop_duplicates(inplace=True)
FilingResultsDF.reset_index(drop=True, inplace=True)

# Get dataframe index values of entries with annual result reported
AnnualValueList = (FilingResultsDF[FilingResultsDF['Q or K'] == 'K']).index.tolist()

# Find the index of the annual values and calculate a fourth quarter value only if there are 3 prior quarterly values
CalculatedFourthQuarterVal = []
ValidAnnualValList = []
for i in range(0, len(AnnualValueList)):
    if AnnualValueList[i] > 2:
        AnnualIndexVal = AnnualValueList[i]
        AnnualVal = float(FilingResultsDF.iloc[AnnualIndexVal, 2])
        FirstThreeQuartersList = []
        for j in range(1, 4):
            if datetime.strptime(FilingResultsDF.iloc[AnnualIndexVal, 1], ISO8601) - datetime.strptime(FilingResultsDF.iloc[AnnualIndexVal - j, 1], ISO8601) < timedelta(days= 365):
                FirstThreeQuartersList += [float(FilingResultsDF.iloc[AnnualIndexVal - j, 2])]
        if len(FirstThreeQuartersList) > 2:
            FourthQuarterVal = AnnualVal - sum(FirstThreeQuartersList)
            CalculatedFourthQuarterVal += [FourthQuarterVal]
            ValidAnnualValList += [AnnualIndexVal]

# Replace the annual value with a calculated fourth quarter value
if len(CalculatedFourthQuarterVal) == len(ValidAnnualValList):
    for i in range(0, len(ValidAnnualValList)):
        FilingResultsDF.at[ValidAnnualValList[i], LookUpValue[0]] = CalculatedFourthQuarterVal[i]
        FilingResultsDF.at[ValidAnnualValList[i], 'Q or K'] = 'Q - Calc'

# If the dataframe is empty then exit
if len(FilingResultsDF) == 0:
    print('Query returned no values, check SEC database to find additional json tags')
    exit()

StopTimer4 = time.perf_counter()

StartTimer5 = time.perf_counter()

# Determines if filing end date falls on a weekend or holiday for use in finding an historic stock quote
ValidEndDateList = []
for i in range(0, len(FilingResultsDF)):
    EndDateForQuote = datetime.strptime(FilingResultsDF.iloc[i, 1], ISO8601).date()
    Today = date.today()
    if Today - EndDateForQuote < timedelta(days=((365 * 5) + 1)):
        DayValue = EndDateForQuote.weekday()
        MarketHolidaysURL = 'http://www.market-holidays.com/' + str(EndDateForQuote.year)
        MarketHolidayResponse = requests.get(MarketHolidaysURL)
        data = MarketHolidayResponse.text
        soup = bs(data, 'html.parser')
        # If end date falls on weekday, check if the day is a holiday. If it does not, put the end date in a list. If it
        # does, keep subtracting one day until it is not on a holiday or weekend
        if DayValue < 5:
            HolidayList = []
            for td in soup.find_all('td'):
                Holiday = td.get_text()
                # This if statement pulls holiday dates
                if str(EndDateForQuote.year) in Holiday:
                    Holiday = datetime.strptime(Holiday, '%B %d, %Y')
                    Holiday = str(Holiday.date())
                    HolidayList += [Holiday]
            if str(EndDateForQuote) not in HolidayList:
                ValidEndDateList += [str(EndDateForQuote)]
            else:
                ValidDate = 0
                DayDelta = 1
                while ValidDate == 0:
                    EndDateForQuote = EndDateForQuote - timedelta(days=DayDelta)
                    DayValue = EndDateForQuote.weekday()
                    if DayValue < 5:
                        HolidayList = []
                        for td in soup.find_all('td'):
                            Holiday = td.get_text()
                            # This if statement pulls holiday dates
                            if str(EndDateForQuote.year) in Holiday:
                                Holiday = datetime.strptime(Holiday, '%B %d, %Y')
                                Holiday = str(Holiday.date())
                                HolidayList += [Holiday]
                        if str(EndDateForQuote) not in HolidayList:
                            ValidEndDateList += [str(EndDateForQuote)]
                            ValidDate = 1
                    DayDelta = DayDelta + 1
        # If end date falls on weekend, keep subtracting one day until it is not on a holiday or weekend
        else:
            ValidDate = 0
            DayDelta = DayValue - 4
            while ValidDate == 0:
                EndDateForQuoteCalc = EndDateForQuote - timedelta(days=DayDelta)
                HolidayList = []
                for td in soup.find_all('td'):
                    Holiday = td.get_text()
                    # This if statement pulls holiday dates
                    if str(EndDateForQuoteCalc.year) in Holiday:
                        Holiday = datetime.strptime(Holiday, '%B %d, %Y')
                        Holiday = str(Holiday.date())
                        HolidayList += [Holiday]
                if str(EndDateForQuoteCalc) not in HolidayList:
                    ValidEndDateList += [str(EndDateForQuoteCalc)]
                    ValidDate = 1
                DayDelta = DayDelta + 1

StopTimer5 = time.perf_counter()

StartTimer6 = time.perf_counter()

# Create a list of historic stock quotes as well as the valid quote date
HistoricQuoteDateList = []
HistoricQuoteList = []
for i in range(0, len(ValidEndDateList)):
    ValidEndDate = datetime.strptime(ValidEndDateList[i], ISO8601)
    ValidEndDateStripped = str(ValidEndDateList[i]).replace('-', '')
    IEXUrl = BaseUrlIEX + Ticker + '/chart/date/' + ValidEndDateStripped + '?chartByDay=true&token=' + IEXToken
    # Pull IEX historic quote value, timer is to prevent rate limiting (1 request every 10 ms)
    IEXStartTimer = time.perf_counter()
    IEXResponse = requests.get(IEXUrl, headers=requests_headers)
    StatusCode = IEXResponse.status_code
    if StatusCode == 200:
        HistoricQuote = IEXResponse.json()[0]['close']
        HistoricQuoteDateList += [str(ValidEndDate.date())]
        HistoricQuoteList += [HistoricQuote]
    else:
        iex_http_response_codes(IEXResponse)
        exit()
    IEXStopTimer = time.perf_counter()
    ProcessTime = IEXStopTimer - IEXStartTimer
    # IEX allows 1 search every 10 ms in cloud mode
    if ProcessTime < IEXRate:
        time.sleep(IEXRate - ProcessTime)

StopTimer6 = time.perf_counter()

StartTimer7 = time.perf_counter()

# Merge dataframes
if len(HistoricQuoteList) == len(HistoricQuoteDateList) == len(FilingResultsDF):
    HistoricQuoteDataframe = pd.DataFrame(HistoricQuoteList, HistoricQuoteDateList)
    HistoricQuoteDataframe.reset_index(level=0, inplace=True)
    HistoricQuoteDataframe.rename(columns={HistoricQuoteDataframe.columns[0]: 'Quote Date',
                                           HistoricQuoteDataframe.columns[1]: 'Historic Quote'}, inplace=True)
    ConcatDataFrame = pd.concat([FilingResultsDF, HistoricQuoteDataframe], axis=1)
    print(ConcatDataFrame)
else:
    print(len(HistoricQuoteList), len(HistoricQuoteDateList), len(FilingResultsDF))
    print('Number of data points do not match')
    exit()

StopTimer7 = time.perf_counter()

print('User Inputs Timer:', StopTimer1 - StartTimer1, 'sec')
print('Initial EDGAR Initial Data Timer:', StopTimer2 - StartTimer2, 'sec')
print('Filing Data Timer:', StopTimer3 - StartTimer3, 'sec')
print('Manipulate Data Timer:', (StopTimer4-StartTimer4), 'sec')
print('Find Valid Market Date Timer:', (StopTimer5-StartTimer5), 'sec')
print('Historic Quote Timer:', (StopTimer6-StartTimer6), 'sec')
print('Merge Dataframe Timer:', (StopTimer7-StartTimer7), 'sec')
print('Overall Process Timer:', StopTimer7-StartTimer1, 'sec')

# Need to consider appropriate behavior if there are not 3 prior quarterly results to the annual result

# Everything below can be considered obsolete since it was created before I figured out there was an SEC api, but it may
# prove to be useful in the future
"""
# EDGAR page for requested ticker
CompanyOverviewURL = 'https://data.sec.gov/submissions/CIK' + CIKLeadingZeros + '.json'

# Get the data, do not remove headers parameter
response = requests.get(CompanyOverviewURL, headers= requests_headers)
        
for i in range(0, len(LookUpValue)):
        

    LookUpFormList = []
    LookUpEndDateList = []
    LookUpValList = []
    for j in range(0, Size):
        Form = LookUp[i]['form']
        EndDate = LookUp[i]['end']
        Val = LookUp[i]['val']
        LookUpFormList += [Form]
        LookUpEndDateList += [EndDate]
        LookUpValList += [Val]
        

LookUpFormList = []
LookUpEndDateList = []
LookUpValList = []
for i in range(0, Size):
    #NetIncome = NetIncome[i]
    Form = LookUp[i]['form']
    EndDate = LookUp[i]['end']
    Val = LookUp[i]['val']
    LookUpFormList += [Form]
    LookUpEndDateList += [EndDate]
    LookUpValList += [Val]

NetIncomeValArray = np.array(LookUpValList).reshape(Size, 1)
NetIncomeEndDateArray = np.array(LookUpEndDateList).reshape(Size, 1)
NetIncomeFormArray = np.array(LookUpFormList).reshape(Size, 1)
NetIncomeArray = np.concatenate((NetIncomeFormArray, NetIncomeEndDateArray, NetIncomeValArray), axis= 1)
print(NetIncomeArray)

df = pd.DataFrame(NetIncomeArray, columns= ['Form', 'End Date', LookUpValue[0]])
print(df)
"""
"""
pd.set_option('display.max_rows', None)
df = pd.DataFrame.from_dict(EDGAR_json)
print(df)
"""
"""
for i in range (0, len(Taxonomy_USGAAP)):
    url = 'https://data.sec.gov/api/xbrl/companyconcept/CIK' + CIKLeadingZeros + '/us-gaap/' + Taxonomy_USGAAP[i] + '.json'
    response = requests.get(url, headers= requests_headers)

    #Output EDGAR data
    EDGAR_json = response.json()
    print(EDGAR_json)
    df = pd.DataFrame.from_dict(EDGAR_json)
    print(df)
    #pprint(EDGAR_json)
"""
"""
#Creates dataframe from list of tickers from SEC site, it is tab delimited
TickerListDF = pd.read_csv('https://sec.gov/include/ticker.txt', sep = '\t', names= ['Ticker', 'CIK'], index_col= 'Ticker')

#User input ticker
Ticker = 'msft'

#Finds corresponding CIK number for the ticker
TickerInfo = TickerListDF.loc[Ticker]
CIK = str(TickerInfo['CIK'])
CIKLeadingZeros = CIK.zfill(10)

print('Ticker: ', Ticker.upper())
print('CIK #: ', CIK)

#EDGAR page for requested ticker
CompanyOverviewURL = 'https://data.sec.gov/submissions/CIK' + CIKLeadingZeros + '.json'

#Spoofs python browser as actual browser
requests_headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

#Get the data, do not remove headers
response = requests.get(CompanyOverviewURL, headers= requests_headers)

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
#End of HTTP response code section

#Output EDGAR data
EDGAR_json = response.json()
#pprint(EDGAR_json)

Form = EDGAR_json['filings']['recent']['form']
#pprint(Form)

#Search the EDGAR json data for all 10-K and 10-Q forms (annual and quarterly) and produces an indexed location
QuarterlyIndex = []
for i in range (0, len(Form)):
    if ('10-K' in Form[i]) or ('10-Q' in Form[i]):
        QuarterlyIndex += [i]
    else:
        None

#Take the index and find the respective accession number used to pull xml from sec site
ReportDateList = []
AccessionNumberList = []
PrimaryDocumentXBRLList = []
PrimaryDocumentHTMLList = []
for i in range (0, len(QuarterlyIndex)):
    InlineXBRLType = EDGAR_json['filings']['recent']['isInlineXBRL'][QuarterlyIndex[i]]
    XBRLType = EDGAR_json['filings']['recent']['isXBRL'][QuarterlyIndex[i]]
    ReportDate = EDGAR_json['filings']['recent']['reportDate'][QuarterlyIndex[i]]
    ReportDateList += [ReportDate]
    AccessionNumber = EDGAR_json['filings']['recent']['accessionNumber'][QuarterlyIndex[i]]
    AccessionNumberList += [AccessionNumber.replace('-', '')]
    PrimaryDocument = EDGAR_json['filings']['recent']['primaryDocument'][QuarterlyIndex[i]]
    if InlineXBRLType == 1:
        PrimaryDocumentHTMLList += [PrimaryDocument]
        PrimaryDocumentXBRLList += [PrimaryDocument.replace('.htm', '_htm.xml')]
    elif Ticker not in PrimaryDocument:
        PrimaryDocumentHTMLList += [PrimaryDocument]
        ReportDateFormatted = ReportDate.replace('-','')
        PrimaryDocument = Ticker + '-' + ReportDateFormatted + '.xml'
        PrimaryDocumentXBRLList += [PrimaryDocument]
    elif '10q_' in PrimaryDocument:
        PrimaryDocumentHTMLList += [PrimaryDocument]
        PrimaryDocument = PrimaryDocument.replace('10q_', '')
        PrimaryDocument = PrimaryDocument.replace('.htm', '.xml')
        PrimaryDocumentXBRLList += [PrimaryDocument]
    elif '10k_' in PrimaryDocument:
        PrimaryDocumentHTMLList += [PrimaryDocument]
        PrimaryDocument = PrimaryDocument.replace('10k_', '')
        PrimaryDocument = PrimaryDocument.replace('.htm', '.xml')
        PrimaryDocumentXBRLList += [PrimaryDocument]
print(PrimaryDocumentXBRLList)
print(ReportDateList)
#Quick if statement to produce URL to EDGAR archives, exits the code if there's a size difference between
#AccessionNumberList and PrimaryDocumentList
if len(AccessionNumberList) != len(PrimaryDocumentXBRLList):
    print('Discrepancy in Accenssion and Primary Document List Sizes')
    exit()
else:
    None

print('Number of Annual/Quarterly Filings: ', len(QuarterlyIndex))

EndDateOverallList = []
NetIncomeOverallList = []
for i in range (0, len(QuarterlyIndex)):
    ArchiveURL_XBRL = 'https://sec.gov/Archives/edgar/data/' + CIK + '/' + AccessionNumberList[i] + '/' + PrimaryDocumentXBRLList[i]
    ArchiveURL_HTML = 'https://sec.gov/Archives/edgar/data/' + CIK + '/' + AccessionNumberList[i] + '/' + PrimaryDocumentHTMLList[i]

    #Print the URLs for debugging
    print('XBRL Link: ', ArchiveURL_XBRL)
    #print('HTML Link: ', ArchiveURL_HTML)

    response = requests.get(ArchiveURL_XBRL, headers=requests_headers)
    response_str = response.text

    Data_XBRL = bs(response_str, 'lxml')
    tag_list = Data_XBRL.find_all()

    NetIncomeList = []
    EndDateList = []
    for tag in tag_list:
        if tag.name == 'us-gaap:netincomeloss':
            try:
                NetIncomeList += [tag.text]
            except:
                NetIncomeList += []
        if tag.name == 'enddate':
            EndDateList += [tag.text]
    try:
        NetIncomeOverallList += [NetIncomeList[0]]
        EndDateOverallList += [EndDateList[0]]
    except:
        NetIncomeOverallList += [0]
        EndDateOverallList += [0]

print(NetIncomeOverallList)
print(EndDateOverallList)
"""
