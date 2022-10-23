from odoo import fields, models, api, _
from datetime import date, datetime, timedelta
import base64
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection([('probation', 'Probation'),('extend_probation', 'Extended Probation'), ('permanent', 'Permanent')], 'State', default='probation')
    permanent_date = fields.Date(string='Permanent Date')
    extend_month = fields.Integer(string='Extend Probation')
    extend_reason = fields.Char(string='Extend Reason')
    trial_end_date = fields.Date('End of Trial Period')
    trial_date_after_extend = fields.Date('Extend Trial Date Period');

    def print_probation_confirm(self):
        pdf_file = self.env.ref('hr_ext.hr_employee_probation').report_action(self)

        return pdf_file


    def print_employee_offer(self):
        
        pdf_file = self.env.ref('hr_ext.hr_employee_offer').report_action(self)

        return pdf_file


    def print_extend_probation(self):
        pdf_file = self.env.ref('hr_ext.hr_employee_extend_probation').report_action(self)

        return pdf_file
        
        
        
