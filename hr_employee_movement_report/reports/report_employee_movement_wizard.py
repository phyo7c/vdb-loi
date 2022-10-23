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
    _name = 'report.employee.movement.wizard'
    _description = 'Employee Movement Report'

    def _get_selection(self):
        current_year = datetime.now().year
        return [(str(i), i) for i in range(current_year - 1, current_year + 10)]

    year = fields.Selection(selection='_get_selection', string='Year', required=True,
                            default=lambda x: str(datetime.now().year))
    month = fields.Selection(selection=MONTH_SELECTION, string='Month', required=True)
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    excel_file = fields.Binary('Excel File')

    @api.onchange('month', 'year')
    def onchange_month_and_year(self):
        if self.year and self.month:
            self.date_from = date(year=int(self.year), month=int(self.month), day=1)
            self.date_to = date(year=int(self.year), month=int(self.month),
                                day=monthrange(int(self.year), int(self.month))[1])

    def get_style(self, workbook):
        color_style = workbook.add_format({'bg_color': 'green'})
        color_style_yellow = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'bg_color': 'yellow'})
        header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1})
        header_style.set_align('vcenter')
        number_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'center',})
        number_style_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'center', 'border': 2 })
        text_left_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'left',})
        return header_style, number_style, color_style, color_style_yellow, text_left_style, number_style_border


    def _write_excel_data(self, workbook, sheet):
        header_style, number_style, color_style, color_style_yellow, text_left_style, number_style_border = self.get_style(
            workbook)

        titles = ['စဥ်', 'အမည်', 'ရာထူး', 'ပညာအရည်အချင်း', 'အလုပ်ဝင်ရက်စွဲ', '', 'စဥ်', 'အမည်',
                  'ရာထူး', 'ပညာအရည်အချင်း', 'အလုပ်ဝင်ရက်စွဲ', 'အလုပ်ထွက်သည့်ရက်စွဲ']

        tcol_no = 0
        y_offset = 0

        company_name = 'မြန်မာအက်ဂရိုအိတ်(စ်)ချိန်းအများနှင့်သက်ဆိုင်သောကုမ္ပဏီလီမိတက်'
        month_count = int(self.month) - 1
        title_name = str(MONTH_SELECTION[month_count][1]) + ' - ' + str(self.year) + '(ဝန်ထမ်းအင်အားစာရင်း)'

        sheet.merge_range(y_offset, 3, y_offset, 6, _(company_name), header_style)
        y_offset += 1
        sheet.merge_range(y_offset, 3, y_offset, 6, _(title_name), header_style)
        y_offset += 1
        sheet.merge_range(y_offset, 0, y_offset, 4, '၀န်ထမ်းအသစ်စာရင်း', header_style)
        sheet.merge_range(y_offset, 6, y_offset, 10, '၀န်ထမ်းအသစ်စာရင်း', header_style)
        y_offset += 1

        for i, title in enumerate(titles):
            sheet.write(y_offset, tcol_no, title, header_style)
            tcol_no += 1
        sheet.set_row(y_offset, 25)
        y_offset += 1
        col_width = [5, 25, 15, 25, 15, 3, 15, 15, 15, 20, 20, 20,]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)
        sheet.write(3, 5, '', color_style)
        sheet.write(4, 5, '', color_style)
        domain = [('joining_date', '>', self.date_from), ('joining_date', '<', self.date_to)]
        tot_domain = [('joining_date', '<', self.date_from)]
        tot_employee_ids = self.env['hr.employee'].sudo().search(tot_domain)
        new_employee_ids = self.env['hr.employee'].sudo().search(domain)
        number = 1
        for emp in new_employee_ids:
            if self.env['hr.education'].search([('id', '=', emp.education.id)]).education:
                education = self.env['hr.education'].search([('id', '=', emp.education.id)]).education
            else:
                education = ''
            if emp.study_field:
                study_field = emp.study_field
            else:
                study_field = ''
            sheet.write(y_offset, 0, number, number_style)
            sheet.write(y_offset, 1, emp.name or '-', text_left_style)
            sheet.write(y_offset, 2, emp.job_title or '-', number_style)
            sheet.write(y_offset, 3, education + ', ' + study_field or '-', number_style)
            sheet.write(y_offset, 4, emp.joining_date and emp.joining_date.strftime('%d-%m-%Y') or '', number_style)
            sheet.write(y_offset, 5, '', color_style)
            number += 1
            y_offset += 1
        domain1 = [('expected_revealing_date', '>', self.date_from), ('expected_revealing_date', '<', self.date_to), ('state', '!=', 'cancel')]
        resign_employee_ids = self.env['hr.resignation'].sudo().search(domain1)
        y_offset += 1
        sheet.write(y_offset, 0, len(new_employee_ids), color_style_yellow)
        sheet.write(y_offset, 6, len(resign_employee_ids), color_style_yellow)
        y_offset_div = 4
        no = 1
        for resign_emp in resign_employee_ids:
            reg_domain = [('resource_id', '=', resign_emp.employee_id.id), '|', ('active', '=', False),  ('active', '=', True) ]
            employee_ids = self.env['hr.employee'].sudo().search(reg_domain)
            if self.env['hr.education'].search([('id', '=', employee_ids.education.id)]):
                education = self.env['hr.education'].search([('id', '=', employee_ids.education.id)]).education
            else:
                education = ''
            if employee_ids.study_field:
                study_field = employee_ids.study_field
            else:
                study_field = ''
            sheet.write(y_offset_div, 6, no, number_style)
            sheet.write(y_offset_div, 7, employee_ids.name or '-' , text_left_style)
            sheet.write(y_offset_div, 8, employee_ids.job_title or '-', number_style)
            sheet.write(y_offset_div, 9, (education + ', ' + study_field) or '-', number_style)
            sheet.write(y_offset_div, 10, employee_ids.joining_date and employee_ids.joining_date.strftime('%d-%m-%Y') or '', number_style)
            sheet.write(y_offset_div, 11, resign_emp.expected_revealing_date and resign_emp.expected_revealing_date.strftime('%d-%m-%Y') or '', number_style)
            number +=1
            y_offset_div += 1

        y_offset += 3
        sheet.write(y_offset, 1, 'Opening for the month of ' + str(MONTH_SELECTION[int(self.month) - 2][1]) + " ' " + str(self.year), text_left_style)
        sheet.write(y_offset, 4, len(tot_employee_ids), number_style)
        y_offset +=1
        sheet.write(y_offset, 1, "Add", text_left_style)
        sheet.write(y_offset, 4, len(new_employee_ids), number_style)
        y_offset += 1
        sheet.write(y_offset, 1, "Resign", text_left_style)
        sheet.write(y_offset, 4, '(' + str(len(resign_employee_ids)) + ')', number_style)
        y_offset += 1
        sheet.write(y_offset, 1, "Closing for the month of " + str(MONTH_SELECTION[int(self.month) - 2][1]) + " ' " + str(self.year), text_left_style)
        sheet.write(y_offset, 4, (len(tot_employee_ids) + len(new_employee_ids)) - len(resign_employee_ids), number_style_border)
        y_offset += 3
        sheet.write(y_offset, 1, "Attendence List staff total", text_left_style)
        y_offset += 1
        tags = {}
        att_domain = [('joining_date', '<', self.date_to)]
        att_total_employee_id = self.env['hr.employee'].sudo().search(att_domain)
        for tot_emp in att_total_employee_id:
            if tot_emp.category_ids.id:
                tags.setdefault(tot_emp.category_ids.id, []).append(tot_emp)
        att_list = 0
        staff_total_list = (len(tot_employee_ids) + len(new_employee_ids)) - len(resign_employee_ids)
        for k in tags:
            sheet.write(y_offset, 1, self.env['hr.employee.category'].search([('id', '=', k)]).name, text_left_style)
            sheet.write(y_offset, 2, len(tags[k]), number_style)
            y_offset += 1
            att_list += len(tags[k])
        sheet.write(y_offset, 1, 'other', text_left_style)
        sheet.write(y_offset, 2, staff_total_list - att_list, number_style)
        y_offset += 1
        sheet.write(y_offset, 2, staff_total_list, color_style_yellow)

    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        month_name = dict(self._fields['month'].selection).get(self.month) + ' - ' + self.year
        report_name = ' Report for ' + month_name + '.xlsx'
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
                'url': 'web/content/?model=report.employee.movement.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, report_name),
                'target': 'new',
            }