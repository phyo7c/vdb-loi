from odoo import models, fields, api, _
from datetime import datetime


MONTH_SELECTION = [
    ('1', 'ဇန်နဝါရီ'),
    ('2', 'ဖေဖော်ဝါရီ'),
    ('3', 'မတ်'),
    ('4', 'ဧပြီ'),
    ('5', 'မေ'),
    ('6', 'ဇွန်'),
    ('7', 'ဇူလိုင်'),
    ('8', 'သြဂုတ်'),
    ('9', 'စက်တင်ဘာ'),
    ('10', 'အောက်တိုဘာ'),
    ('11', 'နိုဝင်ဘာ'),
    ('12', 'ဒီဇင်ဘာ'),
]

MM_NUM_SELECTION = [
    {'1': '၁'},
    {'2': '၂'},
    {'3': '၃'},
    {'4': '၄'},
    {'5': '၅'},
    {'6': '၆'},
    {'7': '၇'},
    {'8': '၈'},
    {'9': '၉'},
    {'10': '၁၀'},
    {'11': '၁၁'},
    {'12': '၁၂'},
]


class EmployeeTaxReport(models.TransientModel):
    _name = 'hr.employee.pathakha.report'

    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year')
    employee_ids = fields.Many2many('hr.employee', 'emp_id', string='Employee(s)')
    month = fields.Selection(selection=MONTH_SELECTION, string='Start Month', required=True,
                             default='10')

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['employee_ids'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(data['employee_ids'])
        self.employee_ids = employees
        data['self_ids'] = self.ids
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data
        }
        return self.env.ref('pathaka_py3o_report_fiscal.action_report_employee_pathakha').report_action(employees, data=datas)

    def number_list(self, data):
        return MM_NUM_SELECTION[data-1][str(data)]

    def month_list(self, i,  month):
        data = int(month)
        check = data + i - 2
        if check > 11:
            return MONTH_SELECTION[check - 12][1]
        else:
            return MONTH_SELECTION[check][1]
