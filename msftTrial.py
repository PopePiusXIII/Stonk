import stock as st
import FairValue as fv
import ReportWriter as rw

if __name__ == "__main__":
    stock = st.Stock('msft', 'microsoft')
    fairValue = fv.Estimate(stock, 10, .1)
    analysis = fv.Analysis(stock)
    analysis.owners_earnings.price,  analysis.owners_earnings.eps = fairValue.owners_earnings_projection()
    analysis.fcf.price,  analysis.fcf.eps = fairValue.fcf_projection()
    analysis.ebitda.price,  analysis.ebitda.eps = fairValue.ebitda_projection()
    analysis.basic.price,  analysis.basic.eps = fairValue.basic_projection()

    report = rw.ReportWriter(analysis)
    report.create_sheets()
    analysis.price_plot()
    print("hi")