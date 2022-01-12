from datetime import datetime, timedelta
import time
import os
import numpy as np
import pandas as pd
import requests
from pprint import pprint
from itertools import chain
import pyEX as p

"""
The SEC requires all companies to submit their quarterly and annual reports (10-Q and 10-K) using a 'standard' taxonomy 
in a xml/xbrl format. Because there is a standardized taxonomy, the SEC put together a browser API that spits out data 
using only the company CIK number and the taxonomy code you are interested in. More information can be found here:
https://www.sec.gov/edgar/sec-api-documentation
"""

#IEX Login - personal login, currently free
c = p.Client(api_token='pk_acd6e54847cd428b8959702163eca5ba', version= 'stable')
IEXToken = 'pk_acd6e54847cd428b8959702163eca5ba'

# User input ticker
Ticker = 'bac'

print(datetime.now())
def http_response_codes(response):
    response_status = str(response.status_code)
    if '200' in response_status:
        print('Website Response = 200: Connected successfully')
    elif '301' in response_status:
        print('Website Response = 301: Redirected to a different endpoint')
    elif '400' in response_status:
        print('Website Response = 400: Bad request, try again')
    elif '401' in response_status:
        print('Website Response = 401: Login required')
    elif '403' in response_status:
        print('Website Response = 403: Forbidden')
    elif '404' in response_status:
        print('Website Response = 404: Cannot access requested site')
    elif '503' in response_status:
        print('Website Response = 503: Server is not ready to handle request')
    else:
        print('N/A')

try:
    TickerListDF = pd.read_csv('https://sec.gov/include/ticker.txt', sep='\t', names=['Ticker', 'CIK'],
                               index_col='Ticker')
except:
    TickerListDF = pd.read_csv('C:\\Users\\modyv\\Documents\\GitHub\\Stonk\\ticker.txt', sep='\t',
                               names=['Ticker', 'CIK'], index_col='Ticker')

# Finds corresponding CIK number for the ticker
TickerInfo = TickerListDF.loc[Ticker]
CIK = str(TickerInfo['CIK'])
CIKLeadingZeros = CIK.zfill(10)

print('Ticker: ', Ticker.upper())
print('CIK #: ', CIK)

# EDGAR page for requested ticker
CompanyOverviewURL = 'https://data.sec.gov/submissions/CIK' + CIKLeadingZeros + '.json'

# Spoofs python browser as actual browser
requests_headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

# Get the data, do not remove headers
response = requests.get(CompanyOverviewURL, headers= requests_headers)

# Returns the response code of the site
http_response_codes(response)

# SEC filing api
url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + CIKLeadingZeros + '.json'
response = requests.get(url, headers= requests_headers)

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

# Values to lookup within the json resutl
LookUpValue = ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax']

# Clean up our Lookup variable for use further on in the code
LookUp = EDGAR_json[LookUpValue[0]]['units']

# Create a list to see if our LookUpValue exists. Since there are 13k+ companies with files dating back to who knows
# when it is best to pass multiple lookup values, however, if the look up value doesn't exist then the code kicks back
# an error. Creating a list called 'LookUpValueExists' allows us to screen the given value before searching
LookUpValueExists = []
for i in range(0, len(LookUpValue)):
    if LookUpValue[i] in ValidTaxonomy[0]:
        LookUpValueExists += [i+1]
    else:
        LookUpValueExists += [0]

# Return the form, the end date, the value, and identify if it is a quarterly or annual result
AllLookUpForm = []
AllLookUpEndDate = []
AllLookUpVals = []
AllQorKColumn = []
for i in range(0, len(LookUpValueExists)):
    if LookUpValueExists[i] > 0:
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
        # Using the for loop below to screen the 'frame' json key. This frame key is used to identify whether the data
        # returned is quarterly annual within an annual filings. We also populate our dataframe 'Quarterly or Annual'
        # column using the frame data
        for j in range(0, LookUpCount):
            if 'frame' in LookUp[j]:
                Frame = LookUp[j]['frame']
                if ('Q' in Frame) or ('q' in Frame):
                    Form = LookUp[j]['form']
                    EndDate = LookUp[j]['end']
                    Val = LookUp[j]['val']
                    LookUpFormList += [Form]
                    LookUpEndDateList += [EndDate]
                    LookUpValList += [Val]
                    QorKColumn += ['Q']
                elif ('Q' not in Frame) or ('q' not in Frame):
                    Form = LookUp[j]['form']
                    EndDate = LookUp[j]['end']
                    PreviousVals = []
                    for k in range(j-3, j-1):
                        PreviousVals += [LookUp[k]['val']]
                    PreviousVals = sum(PreviousVals)
                    Val = LookUp[j]['val']
                    LookUpFormList += [Form]
                    LookUpEndDateList += [EndDate]
                    LookUpValList += [Val]
                    QorKColumn += ['K']
        AllLookUpForm += [LookUpFormList]
        AllLookUpEndDate += [LookUpEndDateList]
        AllLookUpVals += [LookUpValList]
        AllQorKColumn += [QorKColumn]

# Compile into a dataframe
AllLookUpForm = list(chain.from_iterable(AllLookUpForm))
AllLookUpEndDate = list(chain.from_iterable(AllLookUpEndDate))
AllLookUpVals = list(chain.from_iterable(AllLookUpVals))
AllQorKColumn = list(chain.from_iterable(AllQorKColumn))

TotalLookUpCount = len(AllLookUpVals)
LookUpFormArray = np.array(AllLookUpForm).reshape(TotalLookUpCount, 1)
LookUpEndDateArray = np.array(AllLookUpEndDate).reshape(TotalLookUpCount, 1)
LookUpValArray = np.array(AllLookUpVals).reshape(TotalLookUpCount, 1)
QorKColumnArray = np.array(AllQorKColumn).reshape(TotalLookUpCount, 1)
LookUpArray = np.concatenate((LookUpFormArray, LookUpEndDateArray, LookUpValArray, QorKColumnArray), axis= 1)
df = pd.DataFrame(LookUpArray, columns= ['Form', 'End Date', LookUpValue[0], '(Q)uarterly or Annual (K)'])
df.sort_values(by='End Date', inplace=True)
df.reset_index(drop= True, inplace= True)
pd.set_option("display.max_rows", None)

# Identify duplicate End Dates
EndDateList = df.loc[:, 'End Date']
EndDateList = EndDateList.values
# Returns the values of only the duplicates
UniqueEndDates, EndDateCount = np.unique(EndDateList, return_counts= True)
DuplicateEndDates = UniqueEndDates[EndDateCount > 1]

# Identifies the duplicate end dates index values
DuplicateDatesIndices = []
for i in range(0, len(DuplicateEndDates)):
    Duplicates = df[df['End Date'] == DuplicateEndDates[i]].index.values
    Duplicates = Duplicates.tolist()
    DuplicateDatesIndices += Duplicates

# Loops through dataframe to identify entries with identical dates with a Q and K val in the 'Q or K' column
RowsToDelete = []
for i in range(0, len(DuplicateDatesIndices)):
    RepetitiveDatesCheckVal1 = DuplicateDatesIndices[i]
    for j in range (0, len(DuplicateDatesIndices)):
        RepetitiveDatesCheckVal2 = DuplicateDatesIndices[j]
        if i != j:
            if (df.iloc[RepetitiveDatesCheckVal1, 1] == df.iloc[RepetitiveDatesCheckVal2, 1]) and ((df.iloc[RepetitiveDatesCheckVal1, 3] == 'Q') and (df.iloc[RepetitiveDatesCheckVal2, 3] == 'K')):
                RowsToDelete += [RepetitiveDatesCheckVal2]
            elif (df.iloc[RepetitiveDatesCheckVal1, 1] == df.iloc[RepetitiveDatesCheckVal2, 1]) and ((df.iloc[RepetitiveDatesCheckVal1, 3] == 'K') and (df.iloc[RepetitiveDatesCheckVal2, 3] == 'Q')):
                RowsToDelete += [RepetitiveDatesCheckVal1]
            elif (df.iloc[RepetitiveDatesCheckVal1, 1] == df.iloc[RepetitiveDatesCheckVal2, 1]) and (('Q' in df.iloc[RepetitiveDatesCheckVal1, 0]) and ('K' in df.iloc[RepetitiveDatesCheckVal2, 0])):
                RowsToDelete += [RepetitiveDatesCheckVal2]
            elif (df.iloc[RepetitiveDatesCheckVal1, 1] == df.iloc[RepetitiveDatesCheckVal2, 1]) and (('K' in df.iloc[RepetitiveDatesCheckVal1, 0]) and ('Q' in df.iloc[RepetitiveDatesCheckVal2, 0])):
                RowsToDelete += [RepetitiveDatesCheckVal1]

# Deletes previously identified rows
UniqueRowsToDelete = np.unique(RowsToDelete)
UniqueRowsToDelete = UniqueRowsToDelete.tolist()
df.drop(RowsToDelete, inplace= True)

# Remove duplicate rows if they've managed to pass through and reset the dataframe index
df.drop_duplicates(inplace = True)
df.reset_index(drop= True, inplace= True)

# Get dataframe index values of entries with annual result reported
AnnualValueList = (df[df['(Q)uarterly or Annual (K)'] == 'K']).index.tolist()

# Find the index of the annual values and calculate a fourth quarter value only if there are 3 prior quarterly values
CalculatedFourthQuarterVal = []
ValidAnnualValList = []
for i in range(0, len(AnnualValueList)):
    if AnnualValueList[i] > 2:
        AnnualIndexVal = AnnualValueList[i]
        AnnualVal = int(df.iloc[AnnualIndexVal, 2])
        FirstThreeQuartersList = []
        for j in range(1, 4):
            if datetime.strptime(df.iloc[AnnualIndexVal, 1], '%Y-%m-%d') - datetime.strptime(df.iloc[AnnualIndexVal-j, 1], '%Y-%m-%d') < timedelta(days= 365):
                FirstThreeQuartersList += [int(df.iloc[AnnualIndexVal-j, 2])]
        if len(FirstThreeQuartersList) > 2:
            FourthQuarterVal = AnnualVal - sum(FirstThreeQuartersList)
            CalculatedFourthQuarterVal += [FourthQuarterVal]
            ValidAnnualValList += [AnnualIndexVal]

# Replace the annual value with a calculated fourth quarter value
if len(CalculatedFourthQuarterVal) == len(ValidAnnualValList):
    for i in range(0, len(ValidAnnualValList)):
        df.at[ValidAnnualValList[i], 'Revenues'] = CalculatedFourthQuarterVal[i]
        df.at[ValidAnnualValList[i], '(Q)uarterly or Annual (K)'] = 'Q - Calculated'

# Pulling in the historic quote - work in progress
EndDateForQuote = []
for i in range(0, len(df)):
    EndDateForQuote = str(datetime.strptime(df.iloc[i, 1], '%Y-%m-%d').date())
    print(EndDateForQuote.replace('-', ''))
    IEXURL = 'https://cloud.iexapis.com/stable/stock/bac/chart/date/' + EndDateForQuote + '?token=' + IEXToken


# Need to consider appropriate behavior if there are not 3 prior quarterly results to the annual result

# Everything below can be considered obsolete since it was created before I figured out there was an SEC api, but it may
# prove to be useful in the future
"""        
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
