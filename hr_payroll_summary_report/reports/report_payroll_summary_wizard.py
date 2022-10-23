import io
import base64
import xlsxwriter
from odoo import models, fields, api, _
from calendar import monthrange
from datetime import datetime, date

MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]


class ReportPayrollWizard(models.TransientModel):
    _name = 'report.payroll.summary.wizard'
    _description = 'Payroll Summary Report'

    def _get_selection(self):
        current_year = datetime.now().year
        return [(str(i), i) for i in range(2020, current_year + 10)]

    year = fields.Selection(selection='_get_selection', string='Year', required=True,
                            default=lambda x: str(datetime.now().year))
    month = fields.Selection(selection=MONTH_SELECTION, string='Month', required=True)
    branch_id = fields.Many2one('res.branch', string='Branch')
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    department_id = fields.Many2one('hr.department', string='Department')
    filter_by = fields.Selection([
        ('department', 'Department'),
        ('tag', 'Tag')],
        string="Filter By", default="department", required=True)
    excel_file = fields.Binary('Excel File')

    @api.onchange('month', 'year')
    def onchange_month_and_year(self):
        if self.year and self.month:
            self.date_from = date(year=int(self.year), month=int(self.month)-1, day=26)
            self.date_to = date(year=int(self.year), month=int(self.month),
                                day=25)

    def get_style(self, workbook):
        header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1})
        header_style.set_align('vcenter')
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'align': 'vcenter', 'border': 1})
        number_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'vcenter', 'border': 1})
        float_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0.00', 'align': 'vcenter', 'border': 1})
        return header_style, default_style, number_style, float_style

    def salary_by_code(self, payslip_lines, code):
        line = payslip_lines.filtered(lambda l: l.code == code)
        if line:
            return line.total
        else:
            return 0

    def salary_rule_by_code(self, payslip_lines, code):
        line = payslip_lines.filtered(lambda l: l.salary_rule_id.code == code)
        if line:
            return line.total
        else:
            return 0

    def get_grouping(self, payslips):
        gp_dict = {}
        if self.filter_by == 'department':
            for payslip in payslips:
                name = payslip.employee_id.department_id.name
                if self.branch_id:
                    if payslip.employee_id.branch_id == self.branch_id:
                        if name in gp_dict:
                            gp_dict[name].append(payslip)
                        else:
                            gp_dict[name] = [payslip]
                else:
                    if name in gp_dict:
                        gp_dict[name].append(payslip)
                    else:
                        gp_dict[name] = [payslip]
        else:
            combine_name_list = ''
            for payslip in payslips:
                if self.branch_id:
                    if payslip.employee_id.branch_id == self.branch_id:
                        gp_dict, combine_name_list = self.get_tag_list(payslip, gp_dict, combine_name_list)
                else:
                    gp_dict, combine_name_list = self.get_tag_list(payslip, gp_dict, combine_name_list)
            if 'Combine' in gp_dict:
                gp_dict[combine_name_list] = gp_dict.pop('Combine')
        return gp_dict

    def get_tag_list(self, payslip, gp_dict, combine_name_list):
        for category_id in payslip.employee_id.category_ids:
            if category_id.tag_code:
                if category_id.tag_code.lower() in ('gate', 'clean', 'rule'):
                    name = 'Combine'
                    if category_id.name not in combine_name_list:
                        if combine_name_list:
                            combine_name_list += ' + ' + category_id.name
                        else:
                            combine_name_list += category_id.name
            else:
                name = category_id.name
            if name in gp_dict:
                gp_dict[name].append(payslip)
            else:
                gp_dict[name] = [payslip]
        return gp_dict, combine_name_list

    def _write_excel_data(self, workbook, sheet):
        header_style, default_style, number_style, float_style = self.get_style(
            workbook)

        titles = ['Sr no.', 'Department', 'Employee Count',
                  'Basic Pay', 'Leave Deduction', 'Attendance Allowance', 'Gross Salary',
                  "Tax", "SSB", 'Net Salary']

        tcol_no = 0
        y_offset = 0

        company_name = 'All Department' if self.filter_by == 'department' else 'All Tag'
        month_count = int(self.month) - 1
        title_name = "Payroll Summary Report (" + str(MONTH_SELECTION[month_count][1]) + ' - ' + str(self.year) + ')'
        if self.branch_id:
            branch_name = "Branch : " + self.branch_id.name
        else:
            branch_name = "Branch : All"

        sheet.merge_range(y_offset, 3, y_offset, 6, _(title_name), header_style)
        y_offset += 1
        sheet.merge_range(y_offset, 3, y_offset, 6, _(company_name), header_style)
        y_offset += 2
        sheet.merge_range(y_offset, 0, y_offset, 1, _(branch_name), header_style)
        y_offset += 1

        for i, title in enumerate(titles):
            if i == 1 and self.filter_by == 'tag':
                sheet.write(y_offset, tcol_no, "Tag", header_style)
            else:
                sheet.write(y_offset, tcol_no, title, header_style)
            tcol_no += 1
        sheet.set_row(y_offset, 25)
        y_offset += 1
        col_width = [2, 30, 15, 15, 15, 15, 15, 15, 15, 15,
                     15, 15, 15, 15, 15, 15, 15, 15, 15, 15]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)

        domain = [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', '!=', 'draft')]

        if self.department_id:
            domain += [('employee_id.department_id', '=', self.department_id.id)]
        payslips = self.env['hr.payslip'].sudo().search(domain)

        total_emp_count = total_basic = total_deduction = total_att_allow = total_gross = 0
        total_tax = total_ssb = total_net = 0
        groups = self.get_grouping(payslips)

        for sr_no, (group, slips) in enumerate(groups.items()):
            sheet.write(y_offset, 0, sr_no + 1, number_style)
            sheet.write(y_offset, 1, group, default_style)
            emp_count = basic = deduction = att_allow = gross = tax = ssb = net =0
            # group sum
            for slip in slips:
                payslip_lines = slip.line_ids
                if slip.employee_id:
                    emp_count += 1
                basic += self.salary_by_code(payslip_lines, 'BASIC')
                deduction += self.salary_by_code(payslip_lines, 'LVD') or self.salary_by_code(payslip_lines, 'SCL')
                att_allow += self.salary_by_code(payslip_lines, 'AA')
                gross += self.salary_by_code(payslip_lines, 'GROSS')
                tax += self.salary_by_code(payslip_lines, 'ICT')
                ssb += self.salary_by_code(payslip_lines, 'SSB')
                net += self.salary_by_code(payslip_lines, 'NET')

            sheet.write(y_offset, 2, emp_count, number_style)
            sheet.write(y_offset, 3, basic, float_style)
            sheet.write(y_offset, 4, deduction, float_style)
            sheet.write(y_offset, 5, att_allow, float_style)
            sheet.write(y_offset, 6, gross, float_style)
            sheet.write(y_offset, 7, tax, float_style)
            sheet.write(y_offset, 8, ssb, float_style)
            sheet.write(y_offset, 9, net, float_style)
            # total sum
            total_emp_count += emp_count
            total_basic += basic
            total_deduction += deduction
            total_att_allow += att_allow
            total_gross += gross
            total_tax += tax
            total_ssb += ssb
            total_net += net

            y_offset += 1

        sheet.merge_range(y_offset, 0, y_offset, 1, 'Total ', header_style)
        sheet.set_column(0, 1, 30)
        sheet.write(y_offset, 2, total_emp_count, number_style)
        sheet.set_column(2, 2, 20)
        sheet.write(y_offset, 3, total_basic, float_style)
        sheet.set_column(3, 3, 30)
        sheet.write(y_offset, 4, total_deduction, float_style)
        sheet.set_column(4, 4, 30)
        sheet.write(y_offset, 5, total_att_allow, float_style)
        sheet.set_column(5, 5, 30)
        sheet.write(y_offset, 6, total_gross, float_style)
        sheet.set_column(6, 6, 30)
        sheet.write(y_offset, 7, total_tax, float_style)
        sheet.set_column(7, 7, 30)
        sheet.write(y_offset, 8, total_ssb, float_style)
        sheet.set_column(8, 8, 30)
        sheet.write(y_offset, 9, total_net, float_style)
        sheet.set_column(9, 9, 30)

        y_offset += 1

    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        month_name = dict(self._fields['month'].selection).get(self.month) + ' - ' + self.year
        report_name = 'Payroll Summary Report for ' + month_name + '.xlsx'
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
                'url': 'web/content/?model=report.payroll.summary.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, report_name),
                'target': 'new',
            }