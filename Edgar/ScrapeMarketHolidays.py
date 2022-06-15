import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta, date
import pandas
import numpy
from pprint import pprint

DateList = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
Holidays = []
for i in range(0, len(DateList)):
    MarketHolidaysURL = 'http://www.market-holidays.com/' + str(DateList[i])
    MarketHolidayResponse = requests.get(MarketHolidaysURL)
    data = MarketHolidayResponse.text
    soup = bs(data, 'html.parser')
    for td in soup.find_all('td'):
        Holiday = td.get_text()
        if str(DateList[i]) in Holiday:
            Holiday = datetime.strptime(Holiday, '%B %d, %Y')
            #Holiday =str(Holid)
            #Holiday = datetime.strptime(str(Holiday.date()), '%Y-%d-%m')
            Holidays += [Holiday]

#print(Holidays)
df = pd.DataFrame(Holidays)
df.to_csv(r'C:\Users\modyv\Documents\GitHub\Stonk\Edgar\Holidays2007-2023.csv')
print(df)
