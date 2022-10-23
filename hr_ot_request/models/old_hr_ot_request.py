import math
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from pytz import timezone, UTC
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
# from odoo.addons.hr_travel_request.models.hr_travel_request import get_utc_datetime, get_local_datetime, float_to_time
from datetime import datetime, date, time, timedelta


def time_to_float(value):
    return value.hour + value.minute / 60 + value.second / 3600

def float_to_time(value):
    if value < 0:
        value = abs(value)

    hour = int(value)
    minute = round((value % 1) * 60)

    if minute == 60:
        minute = 0
        hour = hour + 1
    return time(hour, minute)


def get_utc_datetime(tz, local_datetime):
    return tz.localize(local_datetime.replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)


def get_local_datetime(tz, utc_datetime):
    return UTC.localize(utc_datetime.replace(tzinfo=None), is_dst=True).astimezone(tz=tz)


class OverTimeRequest(models.Model):
    _name = 'ot.request'
    _description = 'Overtime Request'

    def _default_requested_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

    def _get_requested_employee_domain(self):
        current_employee = self._default_requested_employee_id()
        if current_employee:
            return [('id', '=', current_employee.id)]
        return [('id', '=', False)]

#     def _get_department_domain(self):
#         department_ids = []
#         current_employee = self._default_requested_employee_id()
#         if current_employee:
#             employee_list = current_employee
#             employees = self.env['hr.employee'].search([('approve_manager', '=', current_employee.id)])
#             if employees:
#                 employee_list += employees
#             for emp in employee_list:
#                 department_ids += [emp.department_id.id]
#             department_ids = list(set(department_ids))
#  
#         return [('id', 'in', department_ids)]

    name = fields.Char(string='Title')
    start_date = fields.Datetime(string='Start DateTime', required=True)
    end_date = fields.Datetime(string='End DateTime', required=True)
    duration = fields.Float(string='Duration (hrs)')
    reason = fields.Text(string='Reason')
    request_line = fields.One2many('ot.request.line', 'request_id', string='Invitation')
    # requested_employee_id = fields.Many2one('hr.employee', string='Requested by', domain=lambda self: self._get_requested_employee_domain(),
    #                                         default=lambda self: self._default_requested_employee_id())
    requested_employee_id = fields.Many2one('hr.employee', string='Requested by')
    approve_employee_id = fields.Many2one('hr.employee', string='Approved By',
                                          related='requested_employee_id.parent_id')

    department_ids = fields.Many2many('hr.department', string='Departments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Confirmed'),
        ('approve', 'Second Approval'),
        ('finish', 'Finished'),
        ('verify', 'Verified'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    request_state = fields.Many2one('ot.request.line', string='Request State')
    company_id = fields.Many2one('res.company', string='Company', related='requested_employee_id.company_id', store=True)
    
    @api.onchange('department_ids')
    def onchange_department_ids(self):
        employees = self.env['hr.employee'].browse()
        new_lines = self.env['ot.request.line']
        if self.department_ids:
            domain = [('department_id', 'in', self.department_ids.ids)]
            if self.requested_employee_id:
                domain += [('approve_manager', '=', self.requested_employee_id.id)]
            employees = self.env['hr.employee'].search(domain)

        for emp in employees:
            new_line_value = {'employee_id': emp.id,
                              'start_date': self.start_date,
                              'end_date': self.end_date,
                              'email': emp.work_email,
                              }
            new_line = new_lines.new(new_line_value)
            new_lines += new_line
        self.request_line = new_lines

    def button_confirm(self):
        mail_template = self.env.ref('hr_ot_request.ot_request_mail_template')
        for response in self.request_line:
            mail_template.send_mail(response.id, force_send=True, raise_exception=False)
            response.mail_sent = True
        self.state = 'sent'

    def button_finish(self):
        self.state = 'finish'

    def button_approve(self):
        self.state = 'approve'

    def button_cancel(self):
        self.state = 'cancel'

    @api.onchange('start_date', 'end_date')
    def _onchange_duration_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_('End Date should be greater than or equal to Start Date.'))
            time_diff = self.end_date - self.start_date
            hour = time_diff.days * 24
            hours = time_diff.seconds / 3600
            overall_hour = hour + hours
            if overall_hour >= 24:
                raise ValidationError(_('You can request Overtime within 24 hours!'))
            self.duration = round(hour + hours, 1)
            for response in self.request_line:
                response.start_date = self.start_date
                response.end_date = self.end_date

    def button_verify(self):
        self.state = 'verify'


class OvertimeResponse(models.Model):
    _name = 'ot.request.line'
    _description = 'Overtime Response'

    # def _get_employee_domain(self):
    #     employee_list = []
    #     current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
    #     if current_employee:
    #         employees = self.env['hr.employee'].search([(1, '=', current_employee.id)])
    #         # employees = self.env['hr.employee'].search([('approve_manager', '=', current_employee.id)])
    #         if employees:
    #             employee_list = employees.ids + [current_employee.id]
    #         else:
    #             employee_list = [current_employee.id]
    #     return [('id', 'in', employee_list)]

    def unlink(self):
        for remove_id in self:
            if remove_id.request_id.state != 'approve':
                res = super(OvertimeResponse, self).unlink()
                return res
            else:
                remove_id.state = 'cancel'
    
    def _get_employee_domain(self):
        employee_list = []
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if current_employee:
            employees = self.env['hr.employee'].search([('approve_manager', '=', current_employee.id)])
            if employees:
                employee_list = employees.ids + [current_employee.id]
            else:
                employee_list = [current_employee.id]
        return [('id', 'in', employee_list)]

    request_id = fields.Many2one('ot.request', string='Invitation Line', ondelete='cascade', index=True)
    name = fields.Char(related='request_id.name', string='Title', store=True)
    start_date = fields.Datetime(string='Start DateTime', required=True)
    end_date = fields.Datetime(string='End DateTime', required=True)
    duration = fields.Float(related='request_id.duration', string='Duration (hrs)')
    requested_employee_id = fields.Many2one('hr.employee', string='Requested By',
                                            related='request_id.requested_employee_id')
    approve_employee_id = fields.Many2one('hr.employee', string='Approved By',
                                          related='request_id.approve_employee_id')
    state = fields.Selection([
        ('draft', 'Waiting'),
        ('accept', 'Accepted'),
        ('reject', 'Declined'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    remark = fields.Text(string='Remark')
    employee_id = fields.Many2one('hr.employee', string='Employee', domain=lambda self: self._get_employee_domain())
    employee_name = fields.Char(related='employee_id.name', string='Employee Name', store=True)
    email = fields.Char('Email')
    remark_line = fields.Char('Remark')
    mail_sent = fields.Boolean('Mail Sent')
    department_ids = fields.Many2many('hr.department', string='Departments', related='request_id.department_ids')
    reason = fields.Text(string='Reason', related='request_id.reason')
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id', store=True)
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.email = self.employee_id.work_email

    def open_wizard(self):
        form_view_id = self.env.ref("hr_ot_request.action_view_hr_response").id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Decline Reason',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'decline.response',
            'views': [(form_view_id, 'form')],
            'target': 'new',
        }

    def button_accept(self):
        self.state = 'accept'

    def _get_work_hours(self, date, calendar):
        dayofweek = date.weekday()
        domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id), ('dayofweek', '=', str(dayofweek))]
        if calendar.two_weeks_calendar:
            week_type = int(math.floor((date.toordinal() - 1) / 7) % 2)
            domain += [('week_type', '=', str(week_type))]
        work_hours = self.env['resource.calendar.attendance'].search(domain, order='hour_from asc')
        return work_hours

    @api.constrains('employee_id', 'start_date', 'end_date')
    def check_duplicate_employee(self):
        for response in self:
            emp_domain = [('employee_id', '=', response.employee_id.id), ('request_id', '=', response.request_id.id), ('id', '!=', response.id)]
            if self.search_count(emp_domain):
                raise UserError(_('You have requested to one employee multiple times.'))

            resource_calendar = response.employee_id.resource_calendar_id
            tz = timezone(resource_calendar.tz or 'Asia/Yangon')
            local_start_date = beg_date = get_local_datetime(tz, response.start_date).date()
            local_end_date = end_date = get_local_datetime(tz, response.end_date).date()
            date_start = get_utc_datetime(tz, datetime.combine(local_start_date, datetime.min.time()))
            date_stop = get_utc_datetime(tz, datetime.combine(local_end_date, datetime.max.time()))
            time_domain = [('employee_id', '=', response.employee_id.id), ('request_id', '!=', response.request_id.id),
                           ('start_date', '>=', date_start), ('end_date', '<=', date_stop)]

            print("resource calendar : ", resource_calendar)
            print("tz : ", tz)
            print("local start date : ", local_start_date)
            print("local end date : ", local_end_date)
            print("date start : ", date_start)
            print("date stop : ", date_stop)
            print("start date : ", response.start_date)
            print("end date : ", response.end_date)

            for other in self.search(time_domain):
                latest_start = max(response.start_date, other.start_date)
                earliest_end = min(response.end_date, other.end_date)
                if earliest_end >= latest_start:
                    raise UserError(_('Overlap period in Overtime request Found!'))

#             working_schedules = []
#             while beg_date <= end_date:
#                 public_holiday = self.env['public.holidays.line'].search([('date', '=', beg_date), ('type', '=', 'holiday')])
#                 if not public_holiday:
#                     work_hours = self._get_work_hours(beg_date, resource_calendar)
#                     for wh in work_hours:
#                         local_start_date = datetime.combine(beg_date, float_to_time(wh.hour_from))
#                         local_end_date = datetime.combine(beg_date, float_to_time(wh.hour_to))
#                         if working_schedules and round(time_to_float(working_schedules[-1]['to'])) == 24 and round(wh.hour_from) == 0:
#                             working_schedules[-1]['to'] = local_end_date
#                         else:
#                             working_schedules.append({'from': local_start_date, 'to': local_end_date})
#                 beg_date = beg_date + timedelta(days=1)
#             for ws in working_schedules:
#                 sch_from = datetime.strptime(get_utc_datetime(tz, ws['from']).strftime(DT_FORMAT), DT_FORMAT)
#                 sch_to = datetime.strptime(get_utc_datetime(tz, ws['to']).strftime(DT_FORMAT), DT_FORMAT)
# #                 sch_from = ws['from']
# #                 sch_to = ws['to']
#                 latest_start = max(response.start_date, sch_from)
#                 earliest_end = min(response.end_date, sch_to)
#                 print("sch from : ", sch_from)
#                 print("sch to : ", sch_to)
#                 print("latest start : ", latest_start)
#                 print("earliest end : ", earliest_end)
#                 if earliest_end > latest_start:
#                     raise UserError(_('Overlap period in Working Schedule Found!'))


class Decline(models.Model):
    _name = 'decline.response'
    _description = 'Decline Response'

    decline_remark = fields.Text(string='Remark')

    def decline(self):
        declines = self.env['ot.request.line'].browse(self.env.context.get('active_ids'))
        declines.write({'remark': self.decline_remark,
                        'remark_line': self.decline_remark,
                        'state': 'reject',
                        })
        return declines

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
       
    code = fields.Char('Payroll Code')
    show_in_mobile_app = fields.Boolean(string='Show in Mobile App')
    monthly_limit = fields.Float(string='Monthly Limit')
    max_continuous_days = fields.Integer(string='Max Continuous Days')
    pre_requested_days = fields.Integer(string='Pre Requested Days')