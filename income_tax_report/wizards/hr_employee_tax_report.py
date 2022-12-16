import time
from odoo import api, fields, models
from datetime import datetime


class EmployeeTaxReport(models.TransientModel):
    _name = 'hr.employee.tax.report'

    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year')
    emp = fields.Many2many('hr.employee', 'tax_report_emp_rel', 'tax_report_id', 'emp_id', string='Employee(s)')
    report_date = fields.Date('Report Date', default=lambda self: fields.Date.today())

    def _get_report_base_filename(self, emp_name, date_string, sub_area):
        self.ensure_one()
        month = datetime.strptime(date_string, '%Y-%m-%d').strftime('%b %d')
        return '%s_%s %s_%s' % (emp_name, 'Individual Tax Calculation for', month, sub_area)

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        data['fiscal_year_id'] = self.fiscal_year_id.id
        employees = self.env['hr.employee'].browse(data['emp'])
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data
        }
        return self.env.ref('income_tax_report.action_report_employee_tax').report_action(employees, data=datas)