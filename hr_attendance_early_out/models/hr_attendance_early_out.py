# -*- coding: utf-8 -*-
from datetime import datetime, date, time, timedelta
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api
from pytz import timezone, UTC
import pytz
import math

class HrEmployee(models.Model):
    _description = 'Employee Early Out Form'
    _name = 'hr.employee.early.out'

    date = fields.Datetime(string='DateTime')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    branch_id = fields.Many2one('res.branch', string='Branch')
    manager_id = fields.Many2one('hr.employee', string='Manager')
    department_ids = fields.Many2many('hr.department', string='Department')
    reason = fields.Text(string='Reason')
    state = fields.Selection([('draft', 'Draft'),
                            ('request', 'Requested'),
                            ('approve', 'Approved'),
                            ('cancel', 'Canceled')], default='draft', copy=False)
    early_out_time = fields.Float('Early Out Time', compute='_get_early_out_time')

    def action_request(self):
        if self.state == 'draft':
            self.write({'state': 'request'})

    def action_approve(self):
        if self.state == 'request':
            self.write({'state': 'approve'})

    def action_cancel(self):
        if self.state == 'approve':
            self.write({'state': 'cancel'})

    def action_to_draft(self):
        if self.state == 'cancel':
            self.write({'state': 'draft'})

    @api.depends('date', 'employee_id')
    def _get_early_out_time(self):
        for att in self:
            if att.date and att.employee_id:
                calendar = att.employee_id.resource_calendar_id
                tz = timezone(calendar.tz)
                # change_to_flot = time_to_float(date);
                check_out = att.date + timedelta(hours=+6, minutes=+30)  # att.check_out.astimezone(tz)
                out_float = check_out.hour + check_out.minute / 60 + check_out.second / 3600
                # dayofweek = check_in.weekday()
                domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id)]
                working_hours = self.env['resource.calendar.attendance'].search(domain)
                for wh in working_hours:
                    hour_from = wh.hour_from + 0.000001
                    hour_to = wh.hour_to + 0.000001
                    out_diff = 0
                    if round(wh.hour_from) == 0:
                        out_diff = hour_to - out_float
                    elif round(wh.hour_to) == 24:
                        out_diff = 0
                    else:
                        out_diff = hour_to - out_float

                att.early_out_time = out_diff > 0 and out_diff or 0
            else:
                att.early_out_time = 0.0



