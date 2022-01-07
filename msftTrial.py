import stock as st
import FairValue as fv
import ReportWriter as rw

if __name__ == "__main__":
    stock = st.Stock('msft', 'microsoft')
    fairValue = fv.Estimate(stock, [2022, 2032], .1)
    analysis = fv.Analysis(stock)
    analysis.time_period = fairValue.time_period
    analysis.owners_earnings.price,  analysis.owners_earnings.eps = fairValue.owners_earnings_projection()
    analysis.fcf.price,  analysis.fcf.eps = fairValue.fcf_projection()
    analysis.ebitda.price,  analysis.ebitda.eps = fairValue.ebitda_projection()
    analysis.basic.price,  analysis.basic.eps = fairValue.basic_projection()

    analysis.owners_earnings.growth_rate_per_share = fairValue.get_owners_earnings_per_share_growth_rate()
    analysis.fcf.growth_rate_per_share = fairValue.get_free_cash_flow_per_share_growth_rate()
    analysis.ebitda.growth_rate_per_share = fairValue.get_ebitda_per_share_growth_rate()
    analysis.basic.growth_rate_per_share = fairValue.get_eps_growth_rate()
    analysis.rate_of_return = fairValue.get_rate_of_return()

    analysis.owners_earnings.pe = fairValue.get_price_owners_earnings()
    analysis.fcf.pe = fairValue.get_price_free_cash_flow()
    analysis.ebitda.pe = fairValue.get_ev_ebitda()
    analysis.basic.pe = fairValue.get_pe_basic()

    report = rw.ReportWriter(analysis)
    report.write_eps_projection(analysis.fcf, analysis.time_period, 'free cash flow', 'macrohard')
    analysis.price_plot()
    print("hi")