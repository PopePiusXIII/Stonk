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
