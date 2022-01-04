import matplotlib.pyplot as plt
import statistics as stat


class Estimate:
    current_year = 2022

    def __init__(self, stock, time_period, rate_of_return):

        self.stock = stock
        self.time_period = time_period
        self.rate_of_return = rate_of_return

        self.eps_growth_rates = Estimate.__growth_rates(self.stock.eps)
        self.ebitda_growth_rates = Estimate.__growth_rates(self.stock.ebitda)
        self.revenue_growth_rates = Estimate.__growth_rates(self.stock.revenue)
        self.free_cash_flow_growth_rates = Estimate.__growth_rates(self.stock.free_cash_flow_to_equity)
        self.net_income_growth_rates = Estimate.__growth_rates(self.stock.net_income)

    @staticmethod
    def __growth_rates(series):
        growth_rate = []
        for i in range(1, len(series), 1):
            try:
                val2 = float(series[i])
                val1 = float(series[i-1])
                growth_rate.append(val1 / val2 - 1)
            except:
                print("prob just a header")
                pass
        return growth_rate

    def __price_growth(self, eps, year, earnings_ratio):
        return (eps[self.time_period + Estimate.current_year] * earnings_ratio) / ((1 + self.rate_of_return) ** year)

    def __eps_growth(self, eps, year, growth):
        return eps * ((1 + growth) ** year)

    def basic_projection(self):
        price = {}
        eps = {}

        avg_growth_rate = stat.mean(self.eps_growth_rates)
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps_growth(self.stock.eps[0], i, avg_growth_rate)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price_growth(eps, i, self.stock.pe[0])
        return price, eps

    def owners_earnings_projection(self):
        price = {}
        eps = {}

        avg_growth_rate = stat.mean(self.eps_growth_rates)
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps_growth(self.stock.owner_earnings_per_share[0], i, avg_growth_rate)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price_growth(eps, i, self.stock.price_owners_earnings[0])

        return price, eps

    def evebitda_projection(self):
        price = {}
        eps = {}

        avg_growth_rate = stat.mean(self.ebitda_growth_rates)
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps_growth(self.stock.ebitda_per_share[0], i, avg_growth_rate)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price_growth(eps, i, self.stock.ev_ebitda[0])

        return price, eps

    def fcf_projection(self):
        price = {}
        eps = {}

        # Calculate free cash flow EPS and pe
        fcfeps = self.stock.free_cash_flow_to_equity_per_share[0]

        fcfpe = self.stock.market_price / fcfeps

        avg_growth_rate = stat.mean(self.free_cash_flow_growth_rates)
        # Replace pe with poe and EPS with oeps and run eval
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps_growth(fcfeps, i, avg_growth_rate)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price_growth(eps, i, fcfpe)
        return price, eps


class Projection:
    def __init__(self):
        self.eps = {}
        self.price = {}


class Analysis(Projection):
    def __init__(self):
        super().__init__()
        self.fcf = Projection()
        self.owners_earnings = Projection()
        self.basic = Projection()
        self.evebitda = Projection()
        self.avg_fair_value = None
        self.price_estimate_upper_limit = []
        self.price_estimate_lower_limit = []

    def averages(self):
        # Takes average of yearly price estimates
        self.avg_fair_value = [stat.mean(i) for i in
                               zip(self.fcf.price.values(), self.owners_earnings.price.values(),
                                   self.basic.price.values(), self.evebitda.price.values())]

    def fair_value_check(self):
        # Creates margin of safety upper and lower limit
        for i in range(self.time_period):
            mosUL = self.avg_fair_value[i] + (self.avg_fair_value[i] * self.mos)
            mosLL = self.avg_fair_value[i] - (self.avg_fair_value[i] * self.mos)
            self.price_estimate_upper_limit.append(mosUL)
            self.price_estimate_lower_limit.append(mosLL)

        if self.current_price > self.price_estimate_upper_limit[-1]:
            print("Over Estimated Fair Value")
        elif self.current_price < self.price_estimate_lower_limit[-1]:
            print("Under Estimated Fair Value")
        else:
            print("Near Estimated Fair Value")

    def price_plot(self):
        for i in self.fcf.price.keys():
            plt.scatter(i, self.fcf.price[i], c='black', label='fcf')
            plt.scatter(i, self.evebitda.price[i], c='blue', label='ev ebitda')
            plt.scatter(i, self.owners_earnings.price[i], c='green', label='owners earnings')
            plt.scatter(i, self.basic.price[i], c='purple', label='basic')
            # plt.scatter(i, self.avg_fair_value[i], s=50, c='yellow')
        plt.legend()
        plt.show()
