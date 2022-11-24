import io
import base64
import xlsxwriter
from odoo import models, fields, api, _
from calendar import monthrange
from datetime import datetime, date

class ReportPayrollWizard(models.TransientModel):
    _name = 'report.pay.wizard'
    _description = 'Pay Report'

    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    subarea_id = fields.Many2one('hr.subarea', string='Subarea')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    excel_file = fields.Binary('Excel File')


    def get_style(self, workbook):
        header_style1 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 14, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1})
        header_style1.set_align('vcenter')
        header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1})
        header_style.set_align('vcenter')
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'border': 1})
        number_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'num_format': '#,##0', 'align': 'center', 'border': 1})
        float_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        return header_style1,header_style, default_style, number_style, float_style

    def salary_by_code(self, payslip_lines, code):
        line = payslip_lines.filtered(lambda l: l.code == code)
        if line:
            return line.total
        else:
            return 0

    def _write_excel_data(self, workbook, sheet):
        header_style1,  header_style, default_style, number_style, float_style = self.get_style(
            workbook)

        company_name = 'PIT calculation for ' + self.create_uid.company_id.name
        title_name = self.date_to.strftime('%B') + ' ' + str(self.date_to.year)
        month_name = self.date_to.strftime('%B') + ' ' + str(self.date_to.year)
        fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
                                                              ('date_to', '>=', self.date_to)])
        if fiscal_year:
            title_name += ' [FY ' + fiscal_year.name + ']'

        titles = ['Sr no.', 'Employee ID', 'Employee Name','NRC','GIR', 'Total working months for Contract employee', 'No of ParentsNo',
                  '(Yes/No)', 'No of Children No', 'Currency', 'Residency Status','Basic Salary - USD', 'Hardship', 'Skill', 'Transportation Allowance',
                  "Extra Working Day x2", "Hardship All. - for OT", 'Training Allowance', 'Travelling Allowance', 'Idle Day Allowance',
                  'Public Holiday All. x1', 'SSB EE Contrib', 'Monthly Salary - USD', 'FX', 'Total Montly Taxable Income- MMK',
                  'Previous Estimated Annual Total Income (MMK)', 'Estimated Annual Total Income (USD)', 'Estimated Annual Total Income (MMK)',
                  'Total Annual Salary exceeding minimum threhold for PIT exemption ', '20%, not more than MMK10000000', '(MMK 1000000) for only one spouse',
                  '(MMK 500000 per minor child)', '(MMK 1000000 per parent)', 'Employee(2%)', 'Total Tax Relief', 'Annual Taxable Income',
                  'Tax rate', 'Previous Payable PIT - MMK (PC)', 'Payable PIT to IRD - MMK',
                  'Total Payable PIT to the IRD on salary (MMK) -' + month_name, 'Total Payable PIT to the IRD on salary (USD)-' + month_name, "PIT (USD) As per VDB Loi system generated payroll"]

        tcol_no = 0
        y_offset = 0

        sheet.merge_range(y_offset, 0, y_offset, 41, _(company_name), header_style1)
        y_offset += 1
        sheet.merge_range(y_offset, 0, y_offset, 41, _(title_name), header_style1)
        y_offset += 1

        sheet.write(y_offset, 6,'Parent', header_style)
        sheet.write(y_offset, 7, 'Spouse Income Tax Paid ', header_style)
        sheet.write(y_offset, 8, 'Child', header_style)
        sheet.merge_range(y_offset, 12, y_offset, 14, 'Fixed Allowance - USD', header_style)
        sheet.merge_range(y_offset, 15, y_offset, 21, 'Non- Fixed - USD', header_style)
        sheet.merge_range(y_offset, 22, y_offset, 24, title_name, header_style)
        sheet.write(y_offset, 29, 'Basic Exemption', header_style)
        sheet.write(y_offset, 30, 'Spouse', header_style)
        sheet.write(y_offset, 31, 'Child', header_style)
        sheet.write(y_offset, 32, 'Dependent Parent Allowance', header_style)
        sheet.write(y_offset, 33, 'SSC (Annual basis)', header_style)
        y_offset += 1

        for i, title in enumerate(titles):
            sheet.write(y_offset, tcol_no, title, header_style)
            tcol_no += 1
        sheet.set_row(y_offset, 41)
        y_offset += 1
        col_width = [5, 10, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15,
                     15, 15, 15, 15, 15, 15, 15, 15, 15, 15 , 15, 15, 15, 15, 15, 10, 10, 10, 10, 10, 15, 15, 15, 15,15 ]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)

        domain = [('date_from', '=', self.date_from), ('date_to', '=', self.date_to), ('state', '!=', 'draft')]

        if self.subarea_id:
            domain += [('employee_id.subarea_id', '=', self.subarea_id.id)]
        if self.department_id:
            domain += [('employee_id.department_id', '=', self.department_id.id)]
        if self.employee_id:
                domain += [('employee_id', '=', self.employee_id.id)]
        payslips = self.env['hr.payslip'].sudo().search(domain)

        total_monthly = total_monthly_mmk = 0
        number = 1
        row = 5
        for payslip in payslips:
            est_annual = ssb = basic = skill = transportation = extra_working = hardship_ot_allow = training_allow = travelling_allow = hardship = ide_day_allowance = public_holiday = 0
            parent_no = exemption = spouse_exemption = child_exemption = parent_exemption = annual_tax_income = annual_pay_tax = tax_rate = 0
            spouse = 'No'
            payslip_lines = payslip.line_ids
            currency_rate = payslip.currency_rate
            if payslip.employee_id.tax_exemption_spouse:
                spouse = 'Yes'
            if payslip.employee_id.tax_exemption_father:
                parent_no +=1
            elif payslip.employee_id.tax_exemption_mother:
                parent_no += 1
            basic = self.salary_by_code(payslip_lines, 'BASIC') / currency_rate
            hardship = self.salary_by_code(payslip_lines, 'HARDSHIP') / currency_rate
            skill = self.salary_by_code(payslip_lines, 'SKILL') / currency_rate
            transportation = self.salary_by_code(payslip_lines, 'TRANSPORTATION') / currency_rate
            extra_working = self.salary_by_code(payslip_lines, 'EXTRA_WORKING') / currency_rate
            hardship_ot_allow = self.salary_by_code(payslip_lines, 'HARDSHIP_OT') / currency_rate
            training_allow = self.salary_by_code(payslip_lines, 'TRAINING_ALLOWANCE') / currency_rate
            travelling_allow = self.salary_by_code(payslip_lines, 'TRAVELLING_ALLOWANCE') / currency_rate
            ide_day_allowance = self.salary_by_code(payslip_lines, 'IDLE_DAY_ALLOWANCE') / currency_rate
            public_holiday = self.salary_by_code(payslip_lines, 'PUBLIC_HOLIDAY_ALLOWANCE') / currency_rate
            ssb = self.salary_by_code(payslip_lines, 'SSB') / currency_rate
            exemption = self.salary_by_code(payslip_lines, '20P')
            spouse_exemption = self.salary_by_code(payslip_lines, 'SPE')
            child_exemption = self.salary_by_code(payslip_lines, 'CDE')
            parent_exemption = self.salary_by_code(payslip_lines, 'PTE')
            annual_tax_income = self.salary_by_code(payslip_lines, 'ATI')
            annual_pay_tax = self.salary_by_code(payslip_lines, 'APT')

            total_monthly = basic + hardship + skill + transportation + extra_working + hardship_ot_allow + training_allow + travelling_allow + ide_day_allowance + public_holiday + ssb
            total_monthly_mmk = total_monthly * currency_rate
            est_annual = (basic + hardship + skill + transportation) * 6

            if annual_tax_income >= 70000000:
                tax_rate = '25%'
            elif annual_tax_income >= 50000000:
                tax_rate = '25%'
            elif annual_tax_income >= 30000000:
                tax_rate = '15%'
            elif annual_tax_income >= 10000000:
                tax_rate = '10%'
            elif annual_tax_income >= 2000000:
                tax_rate = '5%'
            elif annual_tax_income >= 0:
                tax_rate = '0%'

            sheet.write(y_offset, 0, number, number_style)
            sheet.write(y_offset, 1, payslip.employee_id.barcode, number_style)
            sheet.write(y_offset, 2, payslip.employee_id.name, number_style)
            sheet.write(y_offset, 3, payslip.employee_id.nrc or '-', number_style)
            sheet.write(y_offset, 4, '-', number_style)
            sheet.write(y_offset, 5, '-', number_style)
            sheet.write(y_offset, 6, parent_no or '-', number_style)
            sheet.write(y_offset, 7, spouse, number_style)
            sheet.write(y_offset, 8, payslip.employee_id.children or '-', number_style)
            sheet.write(y_offset, 9, payslip.employee_id.contract_id.currency_id.name or '-', number_style)
            sheet.write(y_offset, 10, payslip.employee_id.residency_status or '-', number_style)
            sheet.write(y_offset, 11, basic or '-', float_style)
            sheet.write(y_offset, 12, hardship or '-', float_style)
            sheet.write(y_offset, 13, skill or '-', float_style)
            sheet.write(y_offset, 14, transportation or '-', float_style)
            sheet.write(y_offset, 15, extra_working or '-', float_style)
            sheet.write(y_offset, 16, hardship_ot_allow or '-', float_style)
            sheet.write(y_offset, 17, training_allow or '-', float_style)
            sheet.write(y_offset, 18, travelling_allow or '-', float_style)
            sheet.write(y_offset, 19, ide_day_allowance or '-', float_style)
            sheet.write(y_offset, 20, public_holiday or '-', float_style)
            sheet.write(y_offset, 21, ssb or '-', float_style)
            sheet.write(y_offset, 22, total_monthly or '-', float_style)
            sheet.write(y_offset, 23, currency_rate or '-', float_style)
            sheet.write(y_offset, 24, total_monthly_mmk or '-', float_style)
            sheet.write(y_offset, 25, payslip.employee_id.pre_income_total or '-', float_style)
            sheet.write(y_offset, 26, (est_annual + total_monthly) or '-', float_style)
            sheet.write(y_offset, 27, '=ROUND(AA'+ str(row)+'*' + str(currency_rate) +',0)+Z'+ str(row)  or '-', float_style)
            sheet.write(y_offset, 28, '=IF(AB'+ str(row)+'>4800000,AB'+ str(row)+',0)', float_style)
            sheet.write(y_offset, 29, exemption or '-', float_style)
            sheet.write(y_offset, 30, spouse_exemption or '-', float_style)
            sheet.write(y_offset, 31, child_exemption or '-', float_style)
            sheet.write(y_offset, 32, parent_exemption or '-', float_style)
            sheet.write(y_offset, 33, 6000*12 , float_style)
            sheet.write(y_offset, 34, '=SUM(AD' + str(row)+ ':AH' + str(row)+ ')', float_style)
            sheet.write(y_offset, 35, annual_tax_income or '-', float_style)
            sheet.write(y_offset, 36, tax_rate or '-', float_style)
            sheet.write(y_offset, 37, payslip.employee_id.pre_tax_paid or '-', float_style)
            sheet.write(y_offset, 38, annual_pay_tax or '-', float_style)
            sheet.write(y_offset, 39, '=ROUND(((AM'+str(row)+'-AL'+str(row)+')/7),0)' or '-', float_style)
            sheet.write(y_offset, 40, '=ROUND(AN'+ str(row)+'/' + str(currency_rate) + ',2)', float_style)
            sheet.write(y_offset, 41, '=ROUND(AN'+ str(row)+'/' + str(currency_rate) + ',2)', float_style)
            row += 1
            number += 1
            y_offset += 1
        number += 1
        y_offset += 1

    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        report_name = 'Pay Report.xlsx'
        month_name = self.date_to.strftime('%B')
        sheet = workbook.add_worksheet(month_name)
        self._write_excel_data(workbook, sheet)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        excel_file = base64.b64encode(generated_file)
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=report.pay.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, report_name),
                'target': 'new',
            }