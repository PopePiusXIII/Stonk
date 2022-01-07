import pandas as pd
import xlsxwriter as xlsx


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

    def write_eps_projection(self, projection, time_period, sheet_name, filename):
        """
        :param years: tuple (start year, end year)
        :param start_value:
        :return:
        """
        workbook = xlsx.Workbook(filename + '.xlsx')
        worksheet = workbook.add_worksheet(sheet_name)
        offset = 2
        last_row_num = time_period[1] - time_period[0] + offset
        worksheet.write('A1', 'Year')
        worksheet.write('B1', 'EPS')
        worksheet.write('C1', 'EPS Growth')
        worksheet.write('E1', 'Price')
        worksheet.write('F1', 'PE Ratio')
        worksheet.write('J1', 'Rate of Return')
        worksheet.write('J2', self.analysis.rate_of_return)

        for i in range(offset, last_row_num, 1):
            row_num = i
            worksheet.write('A{row_num}'.format(row_num=row_num), time_period[0] + i - offset)

            formula = '=B{row_num}*(1+C{row_num})'.format(row_num=row_num-1, length=last_row_num-1)
            worksheet.write_formula('B{row_num}'.format(row_num=row_num), formula)

            worksheet.write('C{row_num}'.format(row_num=row_num), projection.growth_rate_per_share)

            price_formula = '=B{row_num}*F{row_num}/((1+$J$2)^($A${last_row_num}-A{row_num}))'.format(
                last_row_num=last_row_num-1, row_num=row_num)
            worksheet.write_formula('E{row_num}'.format(row_num=row_num), price_formula)

            worksheet.write('F{row_num}'.format(row_num=row_num), projection.pe)
        print("hi")
        worksheet.write('B' + str(offset), projection.eps[time_period[0]])
        workbook.close()
        return 1
