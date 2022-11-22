import time
from odoo import api, fields, models

class EmployeeTaxReport(models.TransientModel):
    _name = 'hr.employee.tax.report'

    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year')
    emp = fields.Many2many('hr.employee', 'tax_report_emp_rel', 'tax_report_id', 'emp_id', string='Employee(s)')

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(data['emp'])
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data
        }
        return self.env.ref('income_tax_report.action_report_employee_tax').report_action(employees, data=datas)