from odoo import models, fields, api, _
from calendar import monthrange
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.osv import expression

class Contract(models.Model):    
    _inherit = 'hr.contract'    
    _description = 'Contract'

#     job_grade_id = fields.Many2one('job.grade', string='Job Grade')

    def _get_default_notice_days(self):
        if self.env['ir.config_parameter'].sudo().get_param(
                'hr_resignation.notice_period'):
            return self.env['ir.config_parameter'].sudo().get_param(
                            'hr_resignation.no_of_days')
        else:
            return 0

    notice_days = fields.Integer(string="Notice Period", default=_get_default_notice_days)

    first_attendance_allowance = fields.Float('First Attendance Allowance')
    second_attendance_allowance = fields.Float('Second Attendance Allowance')
    ot_rate = fields.Float('Overtime Rate')
    ot_duty_per_hour = fields.Float('Duty OT Rate', compute='_compute_ot_duty_rate')
    ot_allowance_per_day = fields.Float('OT Allowance')
    job_grade_id = fields.Many2one('job.grade', string='Job Grade')
    trial_date_end = fields.Date('End of Trial Period', default=lambda self: (date.today()+relativedelta(months=+3)), required=True, readonly=False, help="End date of the trial period (if there is one).")


    @api.depends('wage')
    def _compute_ot_duty_rate(self):
        for contract in self:
            today = fields.Date.today()
            days_of_month = monthrange(today.year, today.month)[1]
            if contract.wage:
                contract.ot_duty_per_hour = (contract.wage / days_of_month) / 8
            else:
                contract.ot_duty_per_hour = 0

    @api.onchange('date_start')
    def onchange_start_date(self):
        for record in self:
            if record.date_start:
                record.trial_date_end = record.date_start + relativedelta(months=+3)