from odoo import api, fields, models, _
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HRExtendProbation(models.TransientModel):
    _name = "hr.extend.probation"
    _description = "HR Extend Probation Wizard"

    extend_month = fields.Integer(string='Extend Month', required=True)
    reason = fields.Text(string='Reason')

    def extend_probation(self):
        employee = self.env['hr.employee'].browse(
            self._context.get('active_id', []))
        if employee:
            employee.write({
                'state':'extend_probation',
                'extend_month': self.extend_month,
                'extend_reason': self.reason,
            })
            emp_contract = self.env['hr.contract'].sudo().search([('employee_id', '=', employee.id), 
                                                                ('state', '=', 'open')], limit=1)
            if emp_contract:
                trial_date_after_extend = emp_contract.trial_date_end + relativedelta(months=self.extend_month)
                employee.write({
                    'trial_end_date': emp_contract.trial_date_end,
                    'trial_date_after_extend': trial_date_after_extend,
                })
                emp_contract.trial_date_end = trial_date_after_extend
                one_signal_values = {'employee_id': employee.id,
                                    'contents': _('Your probation is extended to %s months. End of probation period is %s.') % (self.extend_month, trial_date_after_extend),
                                    'headings': _('WB B2B : Probation Extend')}
                self.env['one.signal.notification.message'].create(one_signal_values)