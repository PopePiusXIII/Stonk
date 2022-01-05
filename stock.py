import yfinance as yf
import MacroTrendScrape as mts


class Stock:
    def __init__(self, ticker, company_name):
        self._yfin_data = yf.Ticker(ticker)
        self.balance_sheet = mts.get_financial_sheet(ticker, company_name, 'balance-sheet')
        self.balance_sheet.replace(r'^\s*$', 0, regex=True, inplace=True)

        self.income_statement = mts.get_financial_sheet(ticker, company_name, 'income-statement')
        self.income_statement.replace(r'^\s*$', 0, regex=True, inplace=True)
        self.ebitda = self.income_statement.iloc[16, 1:].astype(float)
        self.eps = self.income_statement.iloc[21, 1:].astype(float)
        self.revenue = self.income_statement.iloc[0, 1:].astype(float)
        self.shares_outstanding = self.income_statement.iloc[19, 1:].astype(float)

        self.cashflow_sheet = mts.get_financial_sheet(ticker, company_name, 'cash-flow-statement')
        self.cashflow_sheet.replace(r'^\s*$', 0, regex=True, inplace=True)
        self.net_income = self.cashflow_sheet.iloc[0, 1:].astype(float)
        self.depreciation_amortization = self.cashflow_sheet.iloc[1, 1:].astype(float)
        self.other_noncash_items = self.cashflow_sheet.iloc[2, 1:].astype(float)
        self.cash_from_operating = self.cashflow_sheet.iloc[9, 1:].astype(float)
        self.capex = self.cashflow_sheet.iloc[10, 1:].astype(float)
        self.debt_issuance_retirement_net = self.cashflow_sheet.iloc[20, 1:].astype(float)
        self.free_cash_flow_to_equity = self.capex + self.cash_from_operating + self.debt_issuance_retirement_net

        self.pe = mts.get_table(ticker, company_name, 'pe-ratio').iloc[:, -1]
        self.pfcf = mts.get_table(ticker, company_name, 'price-fcf').iloc[:, -1]

        self.market_price = self._yfin_data.info['currentPrice']
        self.enterprise_value = self._yfin_data.info['enterpriseValue'] / 10**6

        self.capital_change = 0
        self.owner_earnings_per_share = (self.net_income + self.depreciation_amortization + self.other_noncash_items +
                                         self.capex + self.capital_change) / self.shares_outstanding
        self.free_cash_flow_to_equity_per_share = self.free_cash_flow_to_equity / self.shares_outstanding
        self.price_free_cash_flow = self.market_price / self.free_cash_flow_to_equity_per_share
        self.price_owners_earnings = self.market_price / self.owner_earnings_per_share
        self.ev_ebitda = self.enterprise_value / self.ebitda
        self.ebitda_per_share = self.ebitda / self.shares_outstanding
        print("Hi")


if __name__ == "__main__":
    msft = Stock('msft', 'microsoft')
    print("loaded")
