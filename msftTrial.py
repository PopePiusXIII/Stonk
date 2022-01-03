from stock import Stock
import FairValue as fv

if __name__ == "__main__":
    msft = Stock('tsla', 'tesla')
    x = fv.Estimate(msft, 5, .1)
    etsyAnalysis = fv.Analysis()
    etsyAnalysis.owners_earnings.price,  etsyAnalysis.owners_earnings.eps = x.owners_earnings_projection()
    etsyAnalysis.fcf.price,  etsyAnalysis.fcf.eps = x.fcf_projection()
    etsyAnalysis.evebitda.price,  etsyAnalysis.evebitda.eps = x.evebitda_projection()
    etsyAnalysis.basic.price,  etsyAnalysis.basic.eps = x.basic_projection()

    etsyAnalysis.price_plot()