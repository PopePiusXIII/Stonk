import pandas as pd


class ReportWriter:
    def __init__(self, analysis):
        self.analysis = analysis

    def create_sheets(self):
        options = {}
        options['strings_to_formulas'] = False
        options['strings_to_urls'] = False
        space_between = 4
        writer = pd.ExcelWriter(self.analysis.stock.company_name + '.xlsx', engine='xlsxwriter', options=options)
        self.analysis.fcf.eps.to_excel(writer, sheet_name='fcf')
        self.analysis.fcf.price.to_excel(writer, sheet_name='fcf', startcol=space_between)
        self.analysis.ebitda.eps.to_excel(writer, sheet_name='ebitda')
        self.analysis.ebitda.price.to_excel(writer, sheet_name='ebitda', startcol=space_between)
        self.analysis.basic.eps.to_excel(writer, sheet_name='basic')
        self.analysis.basic.price.to_excel(writer, sheet_name='basic', startcol=space_between)
        self.analysis.owners_earnings.eps.to_excel(writer, sheet_name='owners_earnings')
        self.analysis.owners_earnings.price.to_excel(writer, sheet_name='owners_earnings', startcol=space_between)
        writer.close()
