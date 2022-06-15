from UserInputs import *
import time
import requests
from datetime import datetime, timedelta, date
from itertools import chain
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as bs
from pprint import pprint


def initialize(YearsBack, CloudOrSandbox, Ticker):
    # Print current date and time, and calculate now minus 5 years + 1 day
    print(datetime.now())
    DeltaDate = datetime.now().date() - timedelta(days=((365 * YearsBack) + 1))

    # Show all rows and columns for dataframe
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

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
        print('IEX running in \"Cloud\" mode, data is accurate. WATCH CREDIT USAGE!')
    elif ('Sandbox' in CloudOrSandbox) or ('sandbox' in CloudOrSandbox):
        BaseUrlIEX = 'https://sandbox.iexapis.com/stable/stock/'
        IEXToken = 'Tpk_9f4a350423954be3b70ec31a1b20102d'
        IEXRate = 0.5
        print('IEX running in \"Sandbox\" mode, quote data is NOT accurate. FOR TESTING ONLY!')
    else:
        print('Input valid mode for IEX')
        exit()

    # Finds corresponding CIK number for the ticker
    TickerInfo = TickerListDF.loc[Ticker.lower()]
    CIK = str(TickerInfo['CIK'])
    CIKLeadingZeros = CIK.zfill(10)
    print('Ticker: ', Ticker.upper())
    print('CIK #: ', CIK)

    return DeltaDate, TickerListDF, BaseUrlIEX, IEXToken, IEXRate, CIKLeadingZeros


# Function finds the valid filing taxonomy between US-GAAP and IFRS-Full then outputs the data in EDGAR_json
def sec_api_response(CIKLeadingZeros, requests_headers):
    # SEC filing api
    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + CIKLeadingZeros + '.json'
    response = requests.get(url, headers=requests_headers)

    # Try US-GAAP and IFRS-Full taxonomies to find out which one is valid
    USGAAPList = []
    IFRSFullList = []
    try:
        # Output EDGAR data
        EDGAR_json = response.json()
        EDGAR_DEI_json = EDGAR_json['facts']['dei']
        EDGAR_json = EDGAR_json['facts']['us-gaap']
        JSONKEYS = EDGAR_json.keys()
        List = list(JSONKEYS)
        USGAAPList += [List]
    except:
        # Output EDGAR data
        EDGAR_json = response.json()
        EDGAR_DEI_json = EDGAR_json['facts']['dei']
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
    return ValidTaxonomy, EDGAR_json, EDGAR_DEI_json, response, url


# Create a list to see if our LookUpValue exists. Since there are 13k+ companies with files dating back to who knows
# when it is best to pass multiple lookup values, however, if the lookup value doesn't exist then the code kicks back
# an error. Creating a list called 'LookUpValueExists' allows us to screen the given value before searching
def lookup_value_exists(LookUpValue, ValidTaxonomy):
    LookUpValueExists = []
    for i in range(0, len(LookUpValue)):
        if LookUpValue[i] in ValidTaxonomy[0]:
            LookUpValueExists += [i]
        else:
            LookUpValueExists += [-1]
    return LookUpValueExists


# Return the form, the end date, the value, and identify if it is a quarterly or annual result
def get_requested_data(LookUpValueExists, EDGAR_json, EDGAR_DEI_json, LookUpValue, DeltaDate, ISO8601):
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
            if LookUpValue[0] == 'D & A':
                for j in range(0, LookUpCount):
                    Frame = LookUp[j]['fp']
                    Form = LookUp[j]['form']
                    EndDate = LookUp[j]['end']
                    Val = LookUp[j]['val']
                    ValLookedUp = [LookUpValueExists[i]]
                    if (('Q' in Frame) or ('q' in Frame)) and (
                            datetime.strptime(EndDate, ISO8601).date() >= DeltaDate):
                        QorKColumn += ['Q']
                        LookUpFormList += [Form]
                        LookUpEndDateList += [EndDate]
                        LookUpValList += [Val]
                        ValLookedUpList += [ValLookedUp]
                    elif (('Q' not in Frame) or ('q' not in Frame)) and (
                            datetime.strptime(EndDate, ISO8601).date() >= DeltaDate):
                        QorKColumn += ['K']
                        LookUpFormList += [Form]
                        LookUpEndDateList += [EndDate]
                        LookUpValList += [Val]
                        ValLookedUpList += [ValLookedUp]

            else:
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

    return FormResults, EndDateResults, ValResults, QorKResults, ValLookedUpResults


def data_to_dataframe(FormResults, EndDateResults, ValResults, QorKResults, ValLookedUpResults, LookUpValue):
    ColumnHeader = LookUpValue[0]
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
    FilingResultsDF = pd.DataFrame(FilingResultsArray, columns=['Form', 'End Date', ColumnHeader, 'Q or K', 'Lookup Val'])

    # Dataframe must be double sorted for next step to work properly
    FilingResultsDF.sort_values(by=['End Date', 'Q or K'], inplace=True)
    FilingResultsDF.reset_index(drop=True, inplace=True)
    return FilingResultsDF


def remove_inferior_rows(LookUpValue, FilingResultsDF):
    # Goes through FilingResultsDF and checks to see if multiple data points for the same date and the same 'Q or K' value.
    # First for loop makes sure j+1 value does not fall outside the dataframe
    # The inferior value (based off the user defined LookUpValue list order) is deleted
    InferiorLookupValIndex = []
    for i in range(1, (len(LookUpValue) + 1)):
        for j in range(0, (len(FilingResultsDF) - i)):
            if ((FilingResultsDF.iloc[j + i, 4] > FilingResultsDF.iloc[j, 4]) and
                    (FilingResultsDF.iloc[j + i, 1] == FilingResultsDF.iloc[j, 1]) and
                    (FilingResultsDF.iloc[j + i, 3] == FilingResultsDF.iloc[j, 3])):
                InferiorLookupValIndex += [j + i]
            elif ((FilingResultsDF.iloc[j + i, 4] < FilingResultsDF.iloc[j, 4]) and
                  (FilingResultsDF.iloc[j + i, 1] == FilingResultsDF.iloc[j, 1]) and
                  (FilingResultsDF.iloc[j + i, 3] == FilingResultsDF.iloc[j, 3])):
                InferiorLookupValIndex += [j]

    FilingResultsDF.drop(InferiorLookupValIndex, inplace=True)
    FilingResultsDF.reset_index(drop=True, inplace=True)

    return FilingResultsDF


def select_quarterly_over_annual(FilingResultsDF):
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
                if (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[
                    RepetitiveDatesCheckVal2, 1]) \
                        and ((FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 3] == 'Q') and
                             (FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 3] == 'K')):
                    RowsToDelete += [RepetitiveDatesCheckVal2]
                elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[
                    RepetitiveDatesCheckVal2, 1]) \
                        and ((FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 3] == 'K') and
                             (FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 3] == 'Q')):
                    RowsToDelete += [RepetitiveDatesCheckVal1]
                elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[
                    RepetitiveDatesCheckVal2, 1]) \
                        and (('Q' in FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 0]) and
                             ('K' in FilingResultsDF.iloc[RepetitiveDatesCheckVal2, 0])):
                    RowsToDelete += [RepetitiveDatesCheckVal2]
                elif (FilingResultsDF.iloc[RepetitiveDatesCheckVal1, 1] == FilingResultsDF.iloc[
                    RepetitiveDatesCheckVal2, 1]) \
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

    return FilingResultsDF


def calculate_quarterly(k, FilingResultsDF, ISO8601, LookUpValueList):
    # Get dataframe index values of entries with annual result reported
    AnnualValueList = (FilingResultsDF[FilingResultsDF['Q or K'] == 'K']).index.tolist()
    ColumnHeader = LookUpValueList[k][0]
    if 'Shares Outstanding' not in ColumnHeader:
        # Find the index of the annual values and calculate a fourth quarter value only if there are 3 prior quarterly values
        CalculatedFourthQuarterVal = []
        ValidAnnualValList = []
        for i in range(0, len(AnnualValueList)):
            if AnnualValueList[i] > 2:
                AnnualIndexVal = AnnualValueList[i]
                AnnualVal = float(FilingResultsDF.iloc[AnnualIndexVal, 2])
                FirstThreeQuartersList = []
                for j in range(1, 4):
                    if datetime.strptime(FilingResultsDF.iloc[AnnualIndexVal, 1], ISO8601) - datetime.strptime(
                            FilingResultsDF.iloc[AnnualIndexVal - j, 1], ISO8601) < timedelta(days=365):
                        FirstThreeQuartersList += [float(FilingResultsDF.iloc[AnnualIndexVal - j, 2])]
                if len(FirstThreeQuartersList) > 2:
                    FourthQuarterVal = AnnualVal - sum(FirstThreeQuartersList)
                    if FourthQuarterVal.is_integer():
                        FourthQuarterVal = int(FourthQuarterVal)
                    CalculatedFourthQuarterVal += [FourthQuarterVal]
                    ValidAnnualValList += [AnnualIndexVal]

        # Replace the annual value with a calculated fourth quarter value
        if len(CalculatedFourthQuarterVal) == len(ValidAnnualValList):
            for i in range(0, len(ValidAnnualValList)):
                FilingResultsDF.at[ValidAnnualValList[i], ColumnHeader] = CalculatedFourthQuarterVal[i]
                FilingResultsDF.at[ValidAnnualValList[i], 'Q or K'] = 'Q - Calc'
        # If the dataframe is empty then exit
        if len(FilingResultsDF) == 0:
            print(ColumnHeader, 'Query returned no values, check SEC database to find additional json tags')
            exit()

    return FilingResultsDF


def historic_quote_date(FilingResultsDF, ISO8601):
    # Determines if filing end date falls on a weekend or holiday for use in finding an historic stock quote
    ValidEndDateList = []
    for i in range(0, len(FilingResultsDF)):
        EndDateForQuote = datetime.strptime(FilingResultsDF.iloc[i, 0], ISO8601).date()
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
    return ValidEndDateList


def historic_quote(ValidEndDateList, ISO8601, requests_headers, BaseUrlIEX, Ticker, IEXToken, IEXRate):
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

    return HistoricQuoteDateList, HistoricQuoteList


def merge_dataframes(HistoricQuoteList, HistoricQuoteDateList, FilingResultsDF):
    # Merge dataframes
    if len(HistoricQuoteList) == len(HistoricQuoteDateList) == len(FilingResultsDF):
        HistoricQuoteDataframe = pd.DataFrame(HistoricQuoteList, HistoricQuoteDateList)
        HistoricQuoteDataframe.reset_index(level=0, inplace=True)
        HistoricQuoteDataframe.rename(columns={HistoricQuoteDataframe.columns[0]: 'Quote Date',
                                               HistoricQuoteDataframe.columns[1]: 'Historic Quote'}, inplace=True)
        ConcatDataFrame = pd.concat([FilingResultsDF, HistoricQuoteDataframe], axis=1)
        #print(ConcatDataFrame)
    else:
        print(len(HistoricQuoteList), len(HistoricQuoteDateList), len(FilingResultsDF))
        print('Number of data points do not match')
        exit()

    return ConcatDataFrame


def pe_ratio(ConcatDataFrame):
    HistoricQuoteList = ConcatDataFrame['Historic Quote'].tolist()
    EPSList = ConcatDataFrame['EPS'].tolist()
    PERatioList = []
    if len(HistoricQuoteList) == len(EPSList):
        for i in range(0, len(HistoricQuoteList)):
            PERatioList += [float(HistoricQuoteList[i])/float(EPSList[i])]
    ConcatDataFrame['PE Ratio'] = PERatioList
    print(ConcatDataFrame)


def general_http_response_codes(response):
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
    elif '429' in response_status:
        print('Website Response = 429: Too many requests (rate limited)')
    elif '503' in response_status:
        print('Website Response = 503: Server is not ready to handle request')
    else:
        print('N/A')


def iex_http_response_codes(IEXResponse):
    response_status = str(IEXResponse.status_code)
    if '200' in response_status:
        print('IEX Response =', response_status,
              'Connected successfully')
    elif '400' in response_status:
        print('IEX Response =', response_status,
              'Invalid values were supplied for the API request/'
              'No symbol provided/'
              'Batch request \"types\" parameter requires a valid value')
    elif '401' in response_status:
        print('IEX Response =', response_status,
              'Hashed token authorization is restricted/'
              'Hashed token authorization is required/'
              'The requested data is marked restricted and the account does not have access/'
              'An API key is required to access the requested endpoint/'
              'The secret key is required to access to requested endpoint/'
              'The referer in the request header is not allowed due to API token domain restrictions')
    elif '402' in response_status:
        print('IEX Response =', response_status,
              'You have exceeded your allotted credit quota/'
              'The requested endpoint is not available to free accounts/'
              'The requested data is not available to your current tier')
    elif '403' in response_status:
        print('IEX Response =', response_status,
              'Hashed token authorization is invalid/'
              'The provided API token has been disabled/'
              'The provided API token is not valid/'
              'A test token was used for a production endpoint/'
              'A production token was used for a sandbox endpoint/'
              'Your pay-as-you-go circuit breaker has been engaged and further requests are not allowed/'
              'Your account is currently inactive')
    elif '404' in response_status:
        print('IEX Response =', response_status,
              'Unknown symbol provided/'
              'Resource not found')
    elif '413' in response_status:
        print('IEX Response =', response_status,
              'Maximum number of \"types\" values provided in a batch request')
    elif '429' in response_status:
        print('IEX Response =', response_status,
              'Too many requests hit the API too quickly. An exponential backoff of your requests is recommended')
    elif '451' in response_status:
        print('IEX Response =', response_status,
              'The requested data requires additional permission to access')
    elif '500' in response_status:
        print('IEX Response =', response_status,
              'Something went wrong on an IEX Cloud server')
    else:
        print('IEX Response =', response_status,
              'Unknown error')


# The order of look up items matter, sorted from most to least important
RevenueList = ['Revenue',
               'Revenues',
               'RevenuesNetOfInterestExpense',
               'SalesRevenueNet',
               'RevenueFromContractWithCustomerExcludingAssessedTax']

NetIncomeList = ['Net Income',
                 'NetIncomeLoss',
                 'ProfitLoss']

EPSList = ['EPS',
           'EarningsPerShareBasic',
           'EarningsPerShareDiluted']

SharesOutstandingList = ['Shares Outstanding',
                         'WeightedAverageNumberOfSharesOutstandingBasic',
                         'CommonStockSharesOutstanding',
                         'PreferredStockValueOutstanding']

EBITList = ['EBIT',
            'OperatingIncomeLoss',
            'CostsAndExpenses']

DepreciationAndAmortization = ['D & A',
                               'DepreciationAndAmortization',
                               'DepreciationDepletionAndAmortization',
                               'Depreciation']
