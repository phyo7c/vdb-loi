import math
from datetime import datetime, date, time, timedelta
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import pytz


def time_to_float(value):
    return value.hour + value.minute / 60 + value.second / 3600


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Attendance Form Customization'

    late_minutes = fields.Float(string='Late Minutes', compute='_compute_work_hours',
                                digits=dp.get_precision('Payroll'), store=True)
    early_out_minutes = fields.Float(string='Early Out Minutes', compute='_compute_work_hours',
                                     digits=dp.get_precision('Payroll'), store=True)
    ot_hour = fields.Float(string='OT hour', compute='_compute_work_hours', store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('decline', 'Decline'),
                              ('approve', 'Approved'),
                              ('verify', 'Verified')], default='draft', copy=False, required=True)
    is_absent = fields.Boolean('Is Absent', default=False)
    missed = fields.Boolean(string='Missed', default=False, copy=False)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Schedule',
                                           related='employee_id.resource_calendar_id', store=True)

    @api.depends('check_in', 'check_out')
    def _compute_work_hours(self):
        for att in self:
            att.late_minutes = att.early_out_minutes = att.ot_hour = 0
            if att.check_in and att.check_out:
                beg_date = att.check_in + timedelta(hours=+6, minutes=+30)
                public_holiday = self.env['public.holidays.line'].search([('date', '=', beg_date.date()), '|',
                                                                          ('line_id.company_id', '=',
                                                                           att.employee_id.company_id.id),
                                                                          ('line_id.company_id', '=', False)],
                                                                         order='id desc', limit=1)
                if public_holiday:
                    att.late_minutes = 0
                    continue

                calendar = att.employee_id.resource_calendar_id
                tz = timezone(calendar.tz)
                check_in = att.check_in + timedelta(hours=+6, minutes=+30)  # att.check_in.astimezone(tz)
                check_out = att.check_out + timedelta(hours=+6, minutes=+30)  # att.check_out.astimezone(tz)
                in_float = time_to_float(check_in)
                out_float = time_to_float(check_out)
                dayofweek = check_in.weekday()
                day_period = in_float < 12 and 'morning' or 'afternoon'

                domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id),
                          ('dayofweek', '=', str(dayofweek)), ('day_period', '=', day_period)]
                if calendar.two_weeks_calendar:
                    week_type = int(math.floor((check_in.toordinal() - 1) / 7) % 2)
                    domain += [('week_type', '=', str(week_type))]

                if att.employee_id.is_roaster:
                    working_hours = self.env['planning.slot'].search([('employee_id', '=', att.employee_id.id),
                                                                      ('check_date', '=', att.check_in.date())])
                else:
                    working_hours = self.env['resource.calendar.attendance'].search(domain)

                for wh in working_hours:
                    if att.employee_id.is_roaster:
                        start = (wh.start_datetime.hour + 6) + (wh.start_datetime.minute + 30) / 60
                        end = (wh.end_datetime.hour + 6) + (wh.end_datetime.minute + 30) / 60
                        wh_hour_from = start
                        wh_hour_to = end
                    else:
                        wh_hour_from = wh.hour_from
                        wh_hour_to = wh.hour_to
                    hour_from = wh_hour_from
                    hour_to = wh_hour_to
                    in_diff = out_diff = 0
                    if round(wh_hour_from) == 0:
                        out_diff = hour_to - out_float
                    elif round(wh_hour_to) == 24:
                        in_diff = in_float - hour_from
                    else:
                        in_diff = in_float - hour_from
                        out_diff = hour_to - out_float

                    att.late_minutes = in_diff > 0 and in_diff or 0
                    att.early_out_minutes = out_diff > 0 and out_diff or 0
                    att.ot_hour = out_diff < 0 and abs(out_diff) or 0

    def approve_attendances(self, force_approve=False):
        domain = []
        if not force_approve:
            domain = [('state', '=', 'draft')]
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]

        attendances = self.search(domain, order='check_in asc')
        for attendance in attendances:
            if force_approve:
                attendance.state = 'approve'
                if attendance.employee_id.no_need_attendance == True:
                    attendance.is_absent = False
            elif attendance.late_minutes or attendance.early_out_minutes or attendance.is_absent or attendance.missed:
                attendance.state = 'decline'
            else:
                attendance.state = 'approve'
                if attendance.employee_id.no_need_attendance == True:
                    attendance.is_absent = False

    def decline_attendances(self):
        domain = ['|', '|', '|', ('late_minutes', '>', 0), ('early_out_minutes', '>', 0), ('is_absent', '=', True), ('missed', '=', True)]
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]
        attendances = self.search(domain, order='check_in asc')
        for attendance in attendances:
            attendance.state = 'decline'


class ChangeLateMinutesWizard(models.TransientModel):
    _name = "change.late.minutes.wizard"
    _description = "Change Late Minutes Wizard"

    late_minutes = fields.Float('Late Minutes')

    def change(self):
        if self._context.get('active_ids'):
            domain = [('id', 'in', self._context.get('active_ids')), ('check_out', '!=', False),
                      ('state', '!=', 'decline')]
            attendances = self.env['hr.attendance'].search(domain)
            if attendances:
                attendances.write({'late_minutes': self.late_minutes})
                self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}


class ChangeEarlyOutMinutesWizard(models.TransientModel):
    _name = "change.early.out.minutes.wizard"
    _description = "Change Early Out Minutes Wizard"

    early_out_minutes = fields.Float('Early Out Minutes')

    def change(self):
        if self._context.get('active_ids'):
            domain = [('id', 'in', self._context.get('active_ids')), ('check_out', '!=', False),
                      ('state', '!=', 'decline')]
            attendances = self.env['hr.attendance'].search(domain)
            if attendances:
                attendances.write({'early_out_minutes': self.early_out_minutes})
                self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}


class ChangeOtHourWizard(models.TransientModel):
    _name = "change.ot.hour.wizard"
    _description = "Change OT Hour Wizard"

    ot_hour = fields.Float('OT Hours')

    def change(self):
        if self._context.get('active_ids'):
            domain = [('id', 'in', self._context.get('active_ids')), ('check_out', '!=', False),
                      ('state', '!=', 'decline')]
            attendances = self.env['hr.attendance'].search(domain)
            if attendances:
                attendances.write({'ot_hour': self.ot_hour})
                self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}


class ChangeWorkedHoursWizard(models.TransientModel):
    _name = "change.worked.hours.wizard"
    _description = "Change Worked Hours Wizard"

    worked_hours = fields.Float('Worked Hours')

    def change(self):
        if self._context.get('active_ids'):
            domain = [('id', 'in', self._context.get('active_ids')), ('check_out', '!=', False),
                      ('state', '!=', 'decline')]
            attendances = self.env['hr.attendance'].search(domain)
            if attendances:
                attendances.write({'worked_hours': self.worked_hours})
                self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}
    
    
class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"
         
    start_datetime = fields.Datetime(string='Starting DateTime')
    end_datetime = fields.Datetime(string='End DateTime')
    start_end = fields.Selection([('start', 'Start'), ('end', 'End')], default='start', required=True)
    
    
class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"
    
    is_roaster = fields.Boolean("Roaster")
    time_diff_att = fields.Boolean("Date Difference")
    
    
    @api.constrains('attendance_ids')
    def _check_attendance(self):
        # Avoid superimpose in attendance
        for calendar in self:
            attendance_ids = calendar.attendance_ids.filtered(lambda attendance: not attendance.resource_id and attendance.display_type is False)
            if calendar.two_weeks_calendar:
                calendar._check_overlap_inherit(attendance_ids.filtered(lambda attendance: attendance.week_type == '0'))
                calendar._check_overlap_inherit(attendance_ids.filtered(lambda attendance: attendance.week_type == '1'))
            else:
                calendar._check_overlap_inherit(attendance_ids)
                
    def _check_overlap_inherit(self, attendance_ids):
        return True


        