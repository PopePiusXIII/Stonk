import requests
import lxml
from lxml import html
from bs4 import BeautifulSoup as bs
import re
import json
import pandas as pd


def get_financial_sheet(ticker, companyname, tabname):
    """
    use this for the financial tables
    :param ticker: symbol of the company i.e MSFT for microsoft
    :param companyname: name of the company i.e microsoft
    :param tabname: on macrotrends what is the last extension of the webpages link ex: cash-flow-statement
    :return:
    """
    r = requests.get('https://www.macrotrends.net/stocks/charts/' + ticker + '/' + companyname + '/' + tabname)
    p = re.compile(r' var originalData = (.*?);\r\n\r\n\r', re.DOTALL)
    data = json.loads(p.findall(r.text)[0])
    headers = list(data[0].keys())
    headers.remove('popup_icon')
    result = []

    for row in data:
        soup = bs(row['field_name'], features="lxml")
        field_name = soup.select_one('a, span').text
        fields = list(row.values())[2:]
        fields.insert(0, field_name)
        result.append(fields)

    pd.option_context('display.max_rows', None, 'display.max_columns', None)
    df = pd.DataFrame(result, columns=headers)
    return df


def get_table(ticker, companyname, tabname):
    """
    use this for pe ratios, revenue, etc
    :param ticker: symbol of the company i.e MSFT for microsoft
    :param companyname: name of the company i.e microsoft
    :param tabname: on macrotrends what is the last extension of the webpages link ex: cash-flow-statement
    :return:
    """
    r = requests.get('https://www.macrotrends.net/stocks/charts/' + ticker + '/' + companyname + '/' + tabname)
    tree = html.fromstring(r.content)
    tables = tree.findall('.//*/table')
    df = pd.read_html(lxml.etree.tostring(tables[0], method='html'))[0]
    return df


if __name__ == "__main__":
    # get_table('MSFT', 'microsoft', 'cash-flow-statement')
    x = get_table('MSFT', 'microsoft', 'pe-ratio')
    print("hi")