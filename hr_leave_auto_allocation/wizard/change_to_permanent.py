from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class HRChangePermanent(models.TransientModel):
    _name = "hr.change.permanent"
    _description = "HR Change Permanent Wizard"

    def get_end_of_trial_date(self):
        employee = self.env['hr.employee'].browse(
            self._context.get('active_id', []))
        emp_contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), 
                                                        ('state', '=', 'open')])
        if emp_contract:
            return emp_contract.trial_date_end
        else:
            return False

    end_of_trial_date = fields.Date(string='End of Trial Period', default=get_end_of_trial_date, readonly=True)
    permanent_date = fields.Date(string='Permanent Date', required=True)

    def change_to_permanent(self):
        employee = self.env['hr.employee'].browse(
            self._context.get('active_id', []))
        employee.write({
            'permanent_date': self.permanent_date,
            'state': 'permanent'
        })
        
        one_signal_values = {'employee_id': employee.id,
                            'contents': _('%s %s is permanent on %s (%s, %s, %s).') % (employee.name, employee.job_id.name, self.permanent_date, employee.department_id.complete_name, employee.branch_id.name, employee.company_id.name),
                            'headings': _('WB B2B : Employee Change to Permanent')}
        self.env['one.signal.notification.message'].create(one_signal_values)

        # one_signal_values = {'employee_id': employee.branch_id.hr_manager_id.id,
        #                     'contents': _('%s %s is permanent on %s (%s, %s, %s).') % (employee.name, employee.job_id.name, self.permanent_date, employee.department_id.complete_name, employee.branch_id.name, employee.company_id.name),
        #                     'headings': _('WB B2B : Employee Change to Permanent')}
        # self.env['one.signal.notification.message'].create(one_signal_values)
