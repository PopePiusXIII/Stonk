import matplotlib.pyplot as plt
import statistics as stat


# Basic Eval, EV/EBITDA, Owner's Earnings, and Basic FCF class CurrentEstimates:
class Estimate:
    current_year = 2022

    # __init__ to run all calcs at once
    def __init__(self, eps, growth, ror, mos, pe, time_period, current_price, net_income, depre_amat, oncc, capex,
                 capital_change, shares, ev, ebitda, fcf, fcf_growth):

        self.eps = eps
        self.growth = growth
        self.ror = ror
        self.mos = mos
        self.pe = pe
        self.time_period = time_period
        self.current_price = current_price
        self.net_income = net_income
        self.depre_amat = depre_amat
        self.oncc = oncc
        self.capex = capex
        self.capital_change = capital_change
        self.shares = shares
        self.ev = ev
        self.ebitda = ebitda
        self.fcf = fcf
        self.fcf_growth = fcf_growth

    def __price(self, eps, year, earnings_ratio):
        return (eps[self.time_period + Estimate.current_year] * earnings_ratio) / ((1 + self.ror) ** year)

    def __eps(self, eps, year, growth):
        return eps * ((1 + growth) ** year)

    def basic_projection(self):
        price = {}
        eps = {}

        # Loops to calculate yearly EPS and price estimate
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps(self.eps, i, self.growth)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price(eps, i, self.pe)
        return price, eps

    def owners_earnings_projection(self):
        price = {}
        eps = {}

        # Calculate Owner's Earnings per share and price per Owner's Earnings
        oeps = (self.net_income + self.depre_amat + self.oncc + self.capex + self.capital_change) / self.shares
        poe = self.current_price / oeps

        # Replace pe with poe and EPS with oeps and run eval; same calc as basic eval
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps(oeps, i, self.growth)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price(eps, i, poe)

        return price, eps

    def evebitda_projection(self):
        price = {}
        eps = {}

        # Calculate EV/EBITDA
        evebitda = self.ev / self.ebitda

        # Replace pe with EV/EBITDA; same calc as basic eval
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps(self.eps, i, self.growth)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price(eps, i, evebitda)

        return price, eps

    def fcf_projection(self):
        price = {}
        eps = {}

        # Calculate free cash flow EPS and pe
        fcfeps = self.fcf / self.shares

        fcfpe = self.current_price / fcfeps

        # Replace pe with poe and EPS with oeps and run eval
        for i in range(0, self.time_period+1, 1):
            eps[i+Estimate.current_year] = self.__eps(fcfeps, i, self.fcf_growth)

        for i in range(0, self.time_period+1, 1):
            price[Estimate.current_year+self.time_period-i] = self.__price(eps, i, fcfpe)
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
            plt.scatter(i, self.fcf.price[i], c='black')
            plt.scatter(i, self.evebitda.price[i], c='blue')
            plt.scatter(i, self.owners_earnings.price[i], c='green')
            plt.scatter(i, self.basic.price[i], c='purple')
            # plt.scatter(i, self.avg_fair_value[i], s=50, c='yellow')

        plt.show()


x = Estimate(6.17, .05, .1, .15, 8.98, 5, 56.83, 4778, 1214, 270, -.46, -304, 661.53, 40.12, 5.59, 5538, .1)
etsyAnalysis = Analysis()
etsyAnalysis.owners_earnings.price,  etsyAnalysis.fcf.eps = x.owners_earnings_projection()
etsyAnalysis.fcf.price,  etsyAnalysis.fcf.eps = x.fcf_projection()
etsyAnalysis.evebitda.price,  etsyAnalysis.evebitda.eps = x.evebitda_projection()
etsyAnalysis.basic.price,  etsyAnalysis.basic.eps = x.basic_projection()

etsyAnalysis.price_plot()