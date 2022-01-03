import yfinance as yf
import MacroTrendScrape as mts


class Stock:
    def __init__(self, ticker, company_name):
        self._yfin_data = yf.Ticker(ticker)
        self.balance_sheet = mts.get_financial_sheet(ticker, company_name, 'balance-sheet')
        self.income_statement = mts.get_financial_sheet(ticker, company_name, 'income-statement')
        self.cashflow_sheet = mts.get_financial_sheet(ticker, company_name, 'cash-flow-statement')
        self.pe = mts.get_table(ticker, company_name, 'pe-ratio').iloc[:, -1]
        self.pfcf = mts.get_table(ticker, company_name, 'price-fcf').iloc[:, -1]
        self.ebitda = self.income_statement.iloc[16, 1:].astype(float)
        self.eps = self.income_statement.iloc[21, 1:].astype(float)
        self.revenue = self.income_statement.iloc[0, 1:].astype(float)
        self.net_cash_flow = self.cashflow_sheet.iloc[26, 1:].astype(float)
        self.net_income = self.cashflow_sheet.iloc[0, 1:].astype(float)
        self.depreciation_amortization = self.cashflow_sheet.iloc[1, 1:].astype(float)
        self.other_noncash_items = self.cashflow_sheet.iloc[2, 1:].astype(float)
        self.capex = self.cashflow_sheet.iloc[17, 1:].astype(float)
        self.shares_outstanding = self.income_statement.iloc[19, 1:].astype(float)
        self.market_price = self._yfin_data.info['bid']
        self.enterprise_value = self._yfin_data.info['enterpriseValue'] / 10**6
        self.capital_change = 0
        self.owner_earnings_per_share = (self.net_income + self.depreciation_amortization + self.other_noncash_items +
                                         self.capex + self.capital_change) / self.shares_outstanding
        self.price_owners_earnings = self.market_price / self.owner_earnings_per_share
        self.evebitda = self.enterprise_value / self.ebitda


if __name__ == "__main__":
    msft = Stock('msft', 'microsoft')
    print("loaded")
