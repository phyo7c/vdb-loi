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
    _name = 'report.payroll.wizard'
    _description = 'Payroll Report'

    def _get_selection(self):
        current_year = datetime.now().year
        return [(str(i), i) for i in range(current_year - 1, current_year + 10)]

    year = fields.Selection(selection='_get_selection', string='Year', required=True,
                            default=lambda x: str(datetime.now().year))
    month = fields.Selection(selection=MONTH_SELECTION, string='Month', required=True)
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    # company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    # payslip_run_id = fields.Many2one('hr.payslip.run', string='Batch')
    #job_id = fields.Many2one('hr.job', string='Position')
    department_id = fields.Many2one('hr.department', string='Department')
    #branch_id = fields.Many2one('res.branch', string='Branch')
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
        workedday_header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1,
             'bg_color': '#ebe188'})
        workedday_header_style.set_align('vcenter')
        rule_header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1,
             'bg_color': '#e3c1d5'})
        rule_header_style.set_align('vcenter')
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'align': 'vcenter', 'border': 1})
        number_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'vcenter', 'border': 1})
        float_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0.00', 'align': 'vcenter', 'border': 1})
        return header_style, workedday_header_style, rule_header_style, default_style, number_style, float_style

    def worked_day_by_code(self, worked_days, code, day=False):
        type = worked_days.filtered(lambda w: w.work_entry_type_id.code == code)
        if type:
            if day:
                return type.number_of_days
            else:
                type.number_of_hours
        else:
            return 0

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

    def _write_excel_data(self, workbook, sheet):
        header_style, workedday_header_style, rule_header_style, default_style, number_style, float_style = self.get_style(
            workbook)

        # titles = ['စဥ်', 'အမည်', 'ရာထူး/တာဝန်', 'Days', 'ခွင့်©', 'ခွင့်(EL)', 'နာရေးခွင့်', 'ဆေးခွင့်',
        #           'ပိတ်', 'နောက်ကျ', 'တက်', 'မူလလစာ', 'ဖြတ်‌‌ငွေ', 'ရက်မှန်ကြေး', 'အသားတင်',
        #           "Tax (Mar'22)", "SSB 2% Mar'2022",'အသားတင်လစာ','လက်မှတ်']

        titles = ['Sr no.', 'Employee Name', 'Position', 'Days', 'Leave(CL)', 'Leave(EL)', 'Leave(WPL)', 'Leave(ML)',
                  'Leave(MTL)', 'Late', 'Total Attendance Days', 'Basic Pay', 'Leave Deduction', 'Attendance Allowance',
                  'Gross Salary', "Tax", "SSB", 'Net Salary', 'Signature']

        tcol_no = 0
        y_offset = 0

        #company_name = str(self.company_id.name) + ' - '
        company_name = 'All Department' if not self.department_id else str(self.department_id.name)
        month_count = int(self.month) - 1
        title_name = "Payroll Report (" + str(MONTH_SELECTION[month_count][1]) + ' - ' + str(self.year) + ')'

        sheet.merge_range(y_offset, 3, y_offset, 6, _(title_name), header_style)
        y_offset += 1
        sheet.merge_range(y_offset, 3, y_offset, 6, _(company_name), header_style)
        y_offset += 1

        for i, title in enumerate(titles):
            if 5 < i < 9:
                sheet.write(y_offset, tcol_no, title, workedday_header_style)
            elif i > 8:
                sheet.write(y_offset, tcol_no, title, rule_header_style)
            else:
                sheet.write(y_offset, tcol_no, title, header_style)
            tcol_no += 1
        sheet.set_row(y_offset, 25)
        y_offset += 1
        col_width = [5, 25, 15, 15, 15, 25, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
                     15, 15, 15, 15, 15, 15, 15, 15, 15, 15]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)

        domain = [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', '!=', 'draft')]

        if self.department_id:
            domain += [('employee_id.department_id', '=', self.department_id.id)]
        payslips = self.env['hr.payslip'].sudo().search(domain)

        total_days = total_basic = total_deduction = total_inc = total_otaw = total_ot = total_otdt = total_otgz = total_ao1 = total_a02 = 0
        total_leave = total_a03 = total_a04 = total_a05 = total_a06 = total_a00 = total_d01 = total_d02 = total_d03 = 0
        total_d00 = total_late = total_aa = total_abs = total_ssb = total_ict = total_net =total_ded= 0
        total_att = total_el = total_bl = total_leave110 = total_leave111 = total_ld = 0
        for sr_no, payslip in enumerate(payslips):
            total_ded = 0
            employee = payslip.employee_id
            worked_days = payslip.worked_days_line_ids
            payslip_lines = payslip.line_ids
            for line in payslip_lines:
                if line.salary_rule_id.code=='OD':
                    total_ded += line.total

            att_days = self.worked_day_by_code(worked_days, 'WORK100', day=True) - \
                       (self.salary_by_code(payslip_lines, 'LVD') + \
                        self.worked_day_by_code(worked_days, 'EL', day=True) + \
                        self.worked_day_by_code(worked_days, 'BL', day=True) + \
                        self.worked_day_by_code(worked_days, 'LEAVE110', day=True) + \
                        0.0 + \
                        self.salary_by_code(payslip_lines, 'LD'))

            deduction_amt = self.salary_rule_by_code(payslip_lines, 'OD') + self.salary_rule_by_code(payslip_lines,'LD') + self.salary_rule_by_code(payslip_lines, 'LVD')
            sheet.write(y_offset, 0, sr_no + 1, number_style)
            sheet.write(y_offset, 1, employee.name_get()[0][1], default_style)
            sheet.write(y_offset, 2, employee.job_title, default_style)
            sheet.write(y_offset, 3, self.worked_day_by_code(worked_days, 'WORK100', day=True), float_style)
            sheet.write(y_offset, 4, self.salary_by_code(payslip_lines, 'LVD'), float_style)
            sheet.write(y_offset, 5, self.worked_day_by_code(worked_days, 'EL', day=True), float_style)
            sheet.write(y_offset, 6, self.worked_day_by_code(worked_days, 'BL', day=True), float_style)
            sheet.write(y_offset, 7, self.worked_day_by_code(worked_days, 'LEAVE110', day=True), float_style)
            sheet.write(y_offset, 8, 0.0, float_style)
            sheet.write(y_offset, 9, self.salary_by_code(payslip_lines, 'LD'), float_style)
            sheet.write(y_offset, 10, att_days, float_style)
            sheet.write(y_offset, 11, self.salary_by_code(payslip_lines, 'BASIC'), float_style)
            sheet.write(y_offset, 12, deduction_amt, float_style)
            sheet.write(y_offset, 13, self.salary_by_code(payslip_lines, 'AA'), float_style)
            sheet.write(y_offset, 14, self.salary_rule_by_code(payslip_lines, 'BASIC')+self.salary_rule_by_code(payslip_lines, 'AA')+self.salary_rule_by_code(payslip_lines, 'OA')-deduction_amt, float_style)
            sheet.write(y_offset, 15, self.salary_by_code(payslip_lines, 'ICT'), float_style)
            sheet.write(y_offset, 16, self.salary_by_code(payslip_lines, 'SSB'), float_style)
            sheet.write(y_offset, 17,  self.salary_by_code(payslip_lines, 'NET'), float_style)
            sheet.write(y_offset, 18, '', float_style)
            total_days += self.worked_day_by_code(worked_days, 'WORK100', day=True)
            total_leave += self.salary_by_code(payslip_lines, 'LVD')
            total_el +=self.worked_day_by_code(worked_days, 'EL', day=True)
            total_bl +=self.worked_day_by_code(worked_days, 'BL', day=True)
            total_leave110 +=self.worked_day_by_code(worked_days, 'LEAVE110', day=True)
            total_leave111 += 0.0
            total_ld += self.salary_by_code(payslip_lines, 'LD')
            total_att += att_days
            total_basic += self.salary_by_code(payslip_lines, 'BASIC')
            total_deduction += deduction_amt
            total_inc += self.salary_by_code(payslip_lines, 'INC')
            total_aa += self.salary_by_code(payslip_lines, 'AA')
            total_otaw += self.salary_by_code(payslip_lines, 'OTALW')
            total_ot += self.salary_by_code(payslip_lines, 'OT')
            total_otdt += self.salary_by_code(payslip_lines, 'OTDT')
            total_otgz += self.salary_by_code(payslip_lines, 'OTGZ')
            total_ao1 += self.salary_by_code(payslip_lines, 'A01')
            total_a02 += self.salary_by_code(payslip_lines, 'A02')
            total_a03 += self.salary_by_code(payslip_lines, 'A03')
            total_a04 += self.salary_by_code(payslip_lines, 'A04')
            total_a05 += self.salary_by_code(payslip_lines, 'A05')
            total_a06 += self.salary_by_code(payslip_lines, 'A06')
            total_a00 += self.salary_by_code(payslip_lines, 'A00')
            total_d01 += self.salary_by_code(payslip_lines, 'D01')
            total_d02 += self.salary_by_code(payslip_lines, 'D02')
            total_d03 += self.salary_by_code(payslip_lines, 'D03')
            total_d00 += self.salary_by_code(payslip_lines, 'D00')
            total_late += self.salary_by_code(payslip_lines, 'LATE')
            total_abs += self.salary_by_code(payslip_lines, 'ABSENCE')
            total_ssb += self.salary_by_code(payslip_lines, 'SSB')
            total_ict += self.salary_by_code(payslip_lines, 'ICT')
            total_net += self.salary_by_code(payslip_lines, 'NET')
            y_offset += 1

        sheet.merge_range(y_offset, 0, y_offset, 3, 'Total ', header_style)
        sheet.set_column(0, 3, 34)
        # sheet.write(y_offset, 3, total_days, float_style)
        # sheet.set_column(3, 3, 34)
        sheet.write(y_offset, 4, total_leave, float_style)
        sheet.set_column(4, 4, 34)
        sheet.write(y_offset, 5, total_el, float_style)
        sheet.set_column(5, 5, 34)
        sheet.write(y_offset, 6, total_bl, float_style)
        sheet.set_column(6, 6, 34)
        sheet.write(y_offset, 7, total_leave110, float_style)
        sheet.set_column(7, 7, 34)
        sheet.write(y_offset, 8, total_leave111, float_style)
        sheet.set_column(8, 8, 34)
        sheet.write(y_offset, 9, total_ld, float_style)
        sheet.set_column(9, 9, 34)
        sheet.write(y_offset, 10, total_att, float_style)
        sheet.set_column(10, 10, 34)
        sheet.write(y_offset, 11, total_basic, float_style)
        sheet.set_column(11, 11, 34)
        sheet.write(y_offset, 12, total_deduction, float_style)
        sheet.set_column(12, 12, 34)
        sheet.write(y_offset, 13, total_aa, float_style)
        sheet.set_column(13, 13, 34)
        sheet.write(y_offset, 14, total_net, float_style)
        sheet.set_column(14, 14, 34)
        sheet.write(y_offset, 15, total_ict, float_style)
        sheet.set_column(15, 15, 34)
        sheet.write(y_offset, 16, total_ssb, float_style)
        sheet.set_column(16, 16, 34)
        sheet.write(y_offset, 17, total_net, float_style)
        sheet.set_column(17, 17, 34)
        sheet.write(y_offset, 18, '', float_style)
        sheet.set_column(18, 18, 34)

        y_offset += 1

    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        month_name = dict(self._fields['month'].selection).get(self.month) + ' - ' + self.year
        report_name = 'Payroll Report for ' + month_name + '.xlsx'
        sheet = workbook.add_worksheet(month_name)
        self._write_excel_data(workbook, sheet)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        excel_file = base64.encodestring(generated_file)
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=report.payroll.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, report_name),
                'target': 'new',
            }