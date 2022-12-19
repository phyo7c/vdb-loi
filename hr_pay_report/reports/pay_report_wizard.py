import io
import base64
import xlsxwriter
from odoo import models, fields, api, _
from calendar import monthrange
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

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

        company_name = 'PIT calculation for ' + self.env.company.name
        title_name = self.date_to.strftime('%B') + ' ' + str(self.date_to.year)
        month_name = self.date_to.strftime('%B') + ' ' + str(self.date_to.year)
        fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
                                                              ('date_to', '>=', self.date_to)])
        if fiscal_year:
            title_name += ' [FY ' + fiscal_year.name + ']'

        titles = ['Sr no.', 'Employee ID', 'Employee Name','NRC','GIR', 'Total working months for Contract employee', 'No of Parents',
                  '(Yes/No)', 'No of Children', 'Currency', 'Residency Status','Basic Salary - USD', 'Hardship', 'Skill',
                  'Transportation Allowance',]

        title2 = ['Monthly Salary - USD', 'FX',
                  'Total Montly Taxable Income- MMK',
                  'Previous Estimated Annual Total Income (MMK)', 'Estimated Annual Total Income (USD)',
                  'Estimated Annual Total Income (MMK)',
                  'Total Annual Salary exceeding minimum threhold for PIT exemption ', '20%, not more than MMK10000000',
                  '(MMK 1000000) for only one spouse',
                  '(MMK 500000 per minor child)', '(MMK 1000000 per parent)', 'Insurance Premium', 'Employee(2%)', 'Total Tax Relief',
                  'Annual Taxable Income',
                  'Tax rate', 'Previous Payable PIT - MMK (PC)', 'Payable PIT to IRD - MMK']

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
        y_offset += 1

        for i, title in enumerate(titles):
            sheet.write(y_offset, tcol_no, title, header_style)
            tcol_no += 1
        sheet.set_row(y_offset, 41)
        y_offset += 1
        col_width = [5, 10, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15,15, 15, 15, 15, 15, 15, 15, 15, 15,
                     15 , 15, 15, 15, 15, 15, 10, 10, 10, 10, 10, 15, 15, 15, 15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15 ]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)

        domain = [('date_from', '=', self.date_from), ('date_to', '=', self.date_to), ('state', '!=', 'draft')]

        if self.subarea_id:
            domain += [('employee_id.subarea_id', '=', self.subarea_id.id)]
        if self.department_id:
            domain += [('employee_id.department_id', '=', self.department_id.id)]
        if self.employee_id:
                domain += [('employee_id', '=', self.employee_id.id)]
        payslips = self.env['hr.payslip'].sudo().search(domain, order='badge_id asc')

        if not payslips:
            raise UserError(_("There is no payslip for this date range"))

        fiscal_domain = [('date_from', '>=', fiscal_year.date_from), ('date_to', '<=', fiscal_year.date_to), ('state', '!=', 'draft')]

        total_monthly_mmk = 0
        number = 1
        row = 5

        for payslip in payslips:
            ssb = basic = skill = transportation  = hardship = 0
            parent_no = exemption = spouse_exemption = child_exemption = parent_exemption = annual_tax_income = annual_pay_tax = tax_rate = 0
            monthly_basic_usd = previous_est_income_mmk = est_income_usd = est_annual_income = annual_ssb = annual_payable = previous_payable = 0
            total_pay_income_tax_usd = total_pay_income_tax = 0
            fiscal_domain += [('employee_id', '>=', payslip.employee_id.id),('date_to', '<', self.date_from)]
            fic_payslips = self.env['hr.payslip'].sudo().search(fiscal_domain, order="date_to asc")
            total_months = (self.date_from.month - fiscal_year.date_from.month)
            spouse = 'No'
            total_remaining_months = 12
            if payslip.employee_id.contract_id.date_end:
                total_remaining_months = relativedelta(fiscal_year.date_to, payslip.employee_id.contract_id.date_end).months
            payslip_lines = payslip.line_ids
            currency_rate = payslip.currency_rate
            if payslip.employee_id.tax_exemption_spouse:
                spouse = 'Yes'
            if payslip.employee_id.tax_exemption_father:
                parent_no +=1
            if payslip.employee_id.tax_exemption_mother:
                parent_no += 1
            basic = self.salary_by_code(payslip_lines, 'BASIC') / currency_rate
            hardship = self.salary_by_code(payslip_lines, 'HARDSHIP') / currency_rate
            skill = self.salary_by_code(payslip_lines, 'SKILL') / currency_rate
            transportation = self.salary_by_code(payslip_lines, 'TRANSPORTATION') / currency_rate
            ssb = self.salary_by_code(payslip_lines, 'SSBEE')
            exemption = self.salary_by_code(payslip_lines, '20P')
            spouse_exemption = self.salary_by_code(payslip_lines, 'SPE')
            child_exemption = self.salary_by_code(payslip_lines, 'CDE')
            parent_exemption = self.salary_by_code(payslip_lines, 'PTE')
            annual_tax_income = self.salary_by_code(payslip_lines, 'ATI')
            annual_pay_tax = self.salary_by_code(payslip_lines, 'APT')
            monthly_basic_usd = self.salary_by_code(payslip_lines, 'BASICUSD')
            total_monthly_mmk = self.salary_by_code(payslip_lines, 'MTI')
            previous_est_income_mmk = self.salary_by_code(payslip_lines, 'PREI')
            est_income_usd = self.salary_by_code(payslip_lines, 'ATIUSD')
            est_income = self.salary_by_code(payslip_lines, 'ATINC')
            insurance_premium = self.salary_by_code(payslip_lines, 'INSP')
            annual_ssb = self.salary_by_code(payslip_lines, 'SSBIT')
            total_tax_relief = self.salary_by_code(payslip_lines, 'TTR')
            previous_payable = self.salary_by_code(payslip_lines, 'PRET')
            annual_payable = self.salary_by_code(payslip_lines, 'APT')
            total_pay_income_tax = self.salary_by_code(payslip_lines, 'PIT')
            total_pay_income_tax_usd = self.salary_by_code(payslip_lines, 'PITUSD')

            if est_income > 4800000:
                est_annual_income = est_income

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
            sheet.write(y_offset, 4, payslip.employee_id.gir or '-', number_style)
            sheet.write(y_offset, 5, total_remaining_months, number_style)
            sheet.write(y_offset, 6, parent_no or '-', number_style)
            sheet.write(y_offset, 7, spouse, number_style)
            sheet.write(y_offset, 8, payslip.employee_id.children or '-', number_style)
            sheet.write(y_offset, 9, payslip.employee_id.contract_id.currency_id.name or '-', number_style)
            sheet.write(y_offset, 10, payslip.employee_id.residency_status or '-', number_style)
            sheet.write(y_offset, 11, basic or '-', float_style)
            sheet.write(y_offset, 12, hardship or '-', float_style)
            sheet.write(y_offset, 13, skill or '-', float_style)
            sheet.write(y_offset, 14, transportation or '-', float_style)
            col = 15
            title_y_offest =3

            non_fixed_categs = self.env['hr.salary.rule.category'].search([('code', '=', 'NFA')])
            non_fixed_title = self.env['hr.salary.rule'].search([('category_id', 'in', non_fixed_categs.ids)])
            for non_fixed_tit in non_fixed_title:
                sheet.write(title_y_offest, col, non_fixed_tit.name, header_style)
                non_fixed_payslips = self.env['hr.payslip.line'].search([('id', '=', payslip_lines.ids), ('code', '=', non_fixed_tit.code)])
                sheet.write(y_offset, col, (non_fixed_payslips.total / currency_rate) or '-', float_style)
                col += 1
            sheet.merge_range(2, 15, 2, col, 'Non- Fixed - USD', header_style)
            sheet.write(title_y_offest, col, 'SSB EE Contrib', header_style)
            sheet.write(y_offset, col, ssb or '-', float_style)
            col += 1
            my_date_months = 0
            for mm in range(0,total_months):
                if not fiscal_year.date_from > self.date_from and fiscal_year.date_from != self.date_from:
                    my_date_months = fiscal_year.date_from + relativedelta(months=mm)
                    sheet.write(2, col, my_date_months.strftime('%B') + ' ' + str(my_date_months.year), header_style)
                    sheet.write(title_y_offest, col, 'Monthly Salary - USD', header_style)
                    slip_domain = [('employee_id', '=', payslip.employee_id.id), ('date_from', '<=', my_date_months), ('date_to', '>=', my_date_months)]
                    fic_payslips = self.env['hr.payslip'].sudo().search(slip_domain, order="date_to asc")
                    if fic_payslips:
                        previous_payslip_lines = fic_payslips.line_ids
                        sheet.write(y_offset, col, self.salary_by_code(previous_payslip_lines, 'NETUSD') or '-',  float_style)
                    else:
                        sheet.write(y_offset, col, '-', float_style)
                    col += 1
            sheet.merge_range(2, col, 2, col+2, title_name, header_style)
            sheet.write(2, col + 7, 'Basic Exemption', header_style)
            sheet.write(2, col + 8, 'Spouse', header_style)
            sheet.write(2, col + 9, 'Child', header_style)
            sheet.write(2, col + 10, 'Dependent Parent Allowance', header_style)
            sheet.write(2, col + 12, 'SSC (Annual basis)', header_style)

            tit_col = col
            for i, tit in enumerate(title2):
                sheet.write(title_y_offest, tit_col, tit, header_style)
                tit_col += 1
            sheet.write(y_offset, col, monthly_basic_usd or '-', float_style)
            col += 1
            sheet.write(y_offset, col, currency_rate or '-', float_style)
            col += 1
            sheet.write(y_offset, col, total_monthly_mmk or '-', float_style)
            col += 1
            sheet.write(y_offset, col, previous_est_income_mmk or '-', float_style)
            col += 1
            sheet.write(y_offset, col, est_income_usd or '-', float_style)
            col += 1
            sheet.write(y_offset, col, est_income or '-', float_style)
            col += 1
            sheet.write(y_offset, col, est_annual_income or '-', float_style)
            col += 1
            sheet.write(y_offset, col, exemption or '-', float_style)
            col += 1
            sheet.write(y_offset, col, spouse_exemption or '-', float_style)
            col += 1
            sheet.write(y_offset, col, child_exemption or '-', float_style)
            col += 1
            sheet.write(y_offset, col, parent_exemption or '-', float_style)
            col += 1
            sheet.write(y_offset, col, insurance_premium or '-', float_style)
            col += 1
            sheet.write(y_offset, col, annual_ssb or '-', float_style)
            col += 1
            sheet.write(y_offset, col, total_tax_relief or '-', float_style)
            col += 1
            sheet.write(y_offset, col, annual_tax_income or '-', float_style)
            col += 1
            sheet.write(y_offset, col, tax_rate or '-', float_style)
            col += 1
            sheet.write(y_offset, col, previous_payable or '-', float_style)
            col += 1
            sheet.write(y_offset, col, annual_payable or '-', float_style)
            col += 1
            for mm in range(0,total_months):
                if not fiscal_year.date_from >= self.date_from:
                    date_months = fiscal_year.date_from + relativedelta(months=mm)
                    prev_month_name = date_months.strftime('%B') + ' ' + str(date_months.year)
                    sheet.write(2, col, prev_month_name + ' Tax', header_style)
                    sheet.write(title_y_offest, col, 'Total Payable PIT to the IRD on salary (MMK) -' + prev_month_name, header_style)
                    slip_domain1 = [('employee_id', '=', payslip.employee_id.id), ('date_from', '<=', date_months), ('date_to', '>=', date_months)]
                    fic_payslips = self.env['hr.payslip'].sudo().search(slip_domain1, order="date_to asc")
                    if fic_payslips:
                        previous_payslip_lines = fic_payslips.line_ids
                        sheet.write(y_offset, col, self.salary_by_code(previous_payslip_lines, 'PIT') or '-',  float_style)
                    else:
                        sheet.write(y_offset, col, '-', float_style)
                    col += 1
            sheet.write(title_y_offest, col, 'Total Payable PIT to the IRD on salary (MMK) -' + month_name, header_style)
            sheet.write(y_offset, col, total_pay_income_tax or '-', float_style)
            col += 1
            sheet.write(title_y_offest, col, 'Total Payable PIT to the IRD on salary (USD)-' + month_name, header_style)
            sheet.write(y_offset, col, total_pay_income_tax_usd or '-', float_style)
            col += 1
            sheet.write(title_y_offest, col, 'PIT (USD) As per VDB Loi system generated payroll', header_style)
            sheet.write(y_offset, col, total_pay_income_tax_usd or '-', float_style)

            row +=1
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