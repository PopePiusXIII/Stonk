import matplotlib.pyplot as plt
import statistics as stat
import pandas as pd


class Estimate:
    def __init__(self, stock, time_period, rate_of_return):
        self.stock = stock
        self.time_period = time_period
        self.interval = time_period[1] - time_period[0]
        self.current_year = time_period[0]
        self.rate_of_return = rate_of_return

    @staticmethod
    def __compound_annual_growth_rate(series):
        time_history = len(series)-1
        rate = (series[1]/series[-1]) ** (1 / time_history) - 1
        return rate

    def __price_growth(self, eps, year, price_to_earnings_ratio):
        return (eps[self.interval + self.current_year] * price_to_earnings_ratio) / ((1 + self.rate_of_return) ** year)

    @staticmethod
    def __eps_growth(eps, year, growth):
        return eps * ((1 + growth) ** year)

    def discount_cash_flow(self, current_eps, avg_growth_rate, price_to_earnings):
        """
        :param current_eps: most recent annual eps (float)
        :param avg_growth_rate: rate of earnings growth (float) 10% is .1
        :param price_to_earnings: price to earnings ratio (float)
        :return:
        """
        price = {}
        eps = {}

        for i in range(0, self.interval+1, 1):
            eps[i+self.current_year] = self.__eps_growth(current_eps, i, avg_growth_rate)

        for i in range(0, self.interval+1, 1):
            price[self.current_year+self.interval-i] = self.__price_growth(eps, i, price_to_earnings)

        return pd.Series(price), pd.Series(eps).iloc[::-1]

    def __find_price_ratio(self, table):
        """
        :param table: data frame from macrotrends either price to fcf or price to earnings
        :return:
        """
        price_ratio = 0
        i = 0
        for date in table.iloc[:, 0]:
            if date == self.stock.finance_report_date:
                price_ratio = table.iloc[i, -1]
                return price_ratio
            i += 1
        if price_ratio == 0:
            print("couldnt find a pe with same date as financial sheet . Basic projection")
        return 0

    def basic_projection(self):
        pe = self.__find_price_ratio(self.stock.pe_table)
        price, eps = self.discount_cash_flow(self.stock.eps[0], self.get_eps_growth_rate(), pe)
        return pd.Series(price), pd.Series(eps)

    def owners_earnings_projection(self):
        oeps = self.stock.owner_earnings_per_share[0]
        oeps_growth_rate = self.get_owners_earnings_per_share_growth_rate()
        pe = self.get_price_owners_earnings()
        price, eps = self.discount_cash_flow(oeps, oeps_growth_rate, pe)
        return pd.Series(price), pd.Series(eps)

    def ebitda_projection(self):
        ebitda_ps = self.stock.ebitda_per_share[0]
        ebitda_growth_rate = self.get_ebitda_per_share_growth_rate()
        ev_ebitda = self.get_ev_ebitda()
        price, eps = self.discount_cash_flow(ebitda_ps, ebitda_growth_rate, ev_ebitda)
        return pd.Series(price), pd.Series(eps)

    def fcf_projection(self):
        fcfe_ps = self.stock.free_cash_flow_to_equity_per_share[0]
        fcfe_pe = self.__find_price_ratio(self.stock.pfcf_table)
        fcfe_growth_rate = self.get_free_cash_flow_per_share_growth_rate()
        price, eps = self.discount_cash_flow(fcfe_ps, fcfe_growth_rate, fcfe_pe)
        return pd.Series(price), pd.Series(eps)

    def get_free_cash_flow_per_share_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.free_cash_flow_to_equity_per_share)

    def get_revenue_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.revenue)

    def get_ebitda_per_share_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.ebitda_per_share)

    def get_owners_earnings_per_share_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.owner_earnings_per_share)

    def get_net_income_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.net_income)

    def get_eps_growth_rate(self):
        return self.__compound_annual_growth_rate(self.stock.eps)

    def get_rate_of_return(self):
        return self.rate_of_return

    def get_price_free_cash_flow(self):
        return self.__find_price_ratio(self.stock.pfcf_table)

    def get_ev_ebitda(self):
        return self.stock.ev_ebitda[0]

    def get_price_owners_earnings(self):
        return self.stock.price_owners_earnings[0]

    def get_pe_basic(self):
        return self.__find_price_ratio(self.stock.pe_table)


class Projection:
    def __init__(self):
        self.eps = pd.Series({})
        self.price = pd.Series({})
        self.growth_rate_per_share = float
        self.pe = float


class Analysis(Projection):
    def __init__(self, stock):
        super().__init__()
        self.stock = stock
        self.fcf = Projection()
        self.owners_earnings = Projection()
        self.basic = Projection()
        self.ebitda = Projection()
        self.rate_of_return = float
        self.time_period = []

    def price_plot(self):
        for i in self.fcf.price.keys():
            plt.scatter(i, self.fcf.price[i], c='black', label='fcf')
            plt.scatter(i, self.ebitda.price[i], c='blue', label='ev ebitda')
            plt.scatter(i, self.owners_earnings.price[i], c='green', label='owners earnings')
            plt.scatter(i, self.basic.price[i], c='purple', label='basic')
        plt.legend()
        plt.show()
