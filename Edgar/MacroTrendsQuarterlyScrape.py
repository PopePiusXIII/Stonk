import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re
import json
import lxml

Ticker = 'aapl'
Company = 'apple'

ISO8601 = '%Y-%m-%d'

URL = 'https://www.macrotrends.net/stocks/charts/' + Ticker+ '/' + Company + '/income-statement?freq=Q'
print(URL)

response = requests.get(URL)
html_data = response.text
#45317

p = re.compile(r' var originalData = (.*?);\r\n\r\n\r', re.DOTALL)
data = json.loads(p.findall(html_data)[0])
headers = list(data[0].keys())
headers.remove('popup_icon')
result = []

for row in data:
        soup = bs(row['field_name'], features="lxml")
        field_name = soup.select_one('a, span').text
        fields = list(row.values())[2:]
        fields.insert(0, field_name)
        result.append(fields)

pd.set_option('display.max_rows', None, 'display.max_columns', None)
MacroTrendsRaw = pd.DataFrame(result, columns=headers)
MacroTrendsRaw.set_index('field_name', inplace=True)
MacroTrendsData = MacroTrendsRaw.transpose()
MacroTrendsData.columns.name = Ticker
MacroTrendsData.index.name = 'Reporting Date'

MacroTrendsData = MacroTrendsData.drop(columns=['Cost Of Goods Sold',
                                            'Gross Profit',
                                            'Research And Development Expenses',
                                            'SG&A Expenses',
                                            'Other Operating Income Or Expenses',
                                            'Operating Expenses',
                                            'Operating Income',
                                            'Total Non-Operating Income/Expense',
                                            'Pre-Tax Income',
                                            'Income Taxes',
                                            'Income After Taxes',
                                                'Other Income',
                                                'Income From Continuous Operations',
                                                'Income From Discontinued Operations'])

for i in range(0, len(MacroTrendsData.columns)):
    if ('EPS' not in MacroTrendsData.columns[i]) and ('Date' not in MacroTrendsData.columns[i]):
        MacroTrendsData[MacroTrendsData.columns[i]] = 1000000 * pd.to_numeric(MacroTrendsData[MacroTrendsData.columns[i]])
    elif 'EPS' in MacroTrendsData.columns[i]:
        MacroTrendsData[MacroTrendsData.columns[i]] = pd.to_numeric(MacroTrendsData[MacroTrendsData.columns[i]])

MacroTrendsData['D-A'] = MacroTrendsData['EBITDA'] - MacroTrendsData['EBIT']

Test = pd.DataFrame(MacroTrendsData)

MacroTrendsData_json = MacroTrendsData.to_json(orient='index')
MacroTrendsData_json = {Ticker:[MacroTrendsData_json]}
print(MacroTrendsData_json)

with open(r'C:\Users\modyv\Documents\GitHub\Stonk\jsontest.json', 'w') as outfile:
    json.dump(MacroTrendsData_json, outfile)
