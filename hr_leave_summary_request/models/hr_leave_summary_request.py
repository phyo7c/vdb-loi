from odoo import fields, models, api, _
from datetime import timedelta, datetime, date, time
from pytz import timezone, UTC
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
from odoo.exceptions import UserError, ValidationError
import calendar
import math
import logging
from pyfcm import FCMNotification

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


class SummaryRequest(models.Model):
    _name = 'summary.request'
    _description = 'Leave Summary Request'
    _order = 'id desc'

    name = fields.Char('Name', default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    company_id = fields.Many2one('res.company', string='Company')
    resource_calendar_id = fields.Many2one('resource.calendar')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    duration = fields.Float(string='Duration (days)', compute='compute_duration')
    unpaid_leave = fields.Float(string='Unpaid leave(days)', compute='compute_duration')
    duration_unpaid_leave = fields.Float(string='Unpaid leave(days)', compute='compute_duration')
    description = fields.Text('Description')
    attachment = fields.Binary(string="Attachment")
    file_name = fields.Char('File Name')
    holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type", required=True)
    leave_line = fields.One2many('summary.request.line', 'request_id', string='Leaves in detail', )
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('approve', 'Approved'),
                              ('refuse', 'Refused'),
                              ('verify', 'Verified')],
                             string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    enable_approval = fields.Boolean('Enable Approval', compute='_compute_enable_approval')
    leave_type_request_unit = fields.Selection(related='holiday_status_id.request_unit', readonly=True)
    
    @api.depends('employee_id')
    @api.depends_context('employee_id')
    def _compute_enable_approval(self):
        for req in self:
            if self.env.context.get('employee_id'):
                domain = [('id', '=', self.env.context.get('employee_id'))]
            else:
                domain = [('user_id', '=', self.env.user.id)]
            employee = self.env['hr.employee'].search(domain, limit=1)
            # is_approval_manager = self.env['hr.employee'].search([('approve_manager', '=', employee.id)]) and True or False
            # if employee and req.employee_id.approve_manager == employee or is_approval_manager and req.employee_id == employee:
            if employee and req.employee_id.approve_manager == employee:
                req.enable_approval = True
            else:
                req.enable_approval = False

    def _create_notification_message(self):
        if self.employee_id.approve_manager:
        #     one_signal_values = {'employee_id': self.employee_id.approve_manager.id,
        #                          'contents': _('LEAVE SUMMARY REQUEST: %s submitted leave summary request.') % self.employee_id.name,
        #                          'headings': _('WB B2B : SUBMITTED LEAVE SUMMARY REQUEST')}
        #     self.env['one.signal.notification.message'].create(one_signal_values)
            content = 'LEAVE SUMMARY REQUEST: %s submitted leave summary request.' % self.employee_id.approve_manager.name
            message_title = 'MAEX : SUBMITTED LEAVE SUMMARY REQUEST'
            if self.employee_id.device_token:
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': message_title}
                self.env['firebase.notification.message'].create(firebase_values)
                self.employee_id.send_noti([self.employee_id.device_token], content, message_title)
            
    def _create_approved_notification_message(self, employee=None):
        if employee:
        #     one_signal_values = {'employee_id': employee.id,
        #                          'contents': _('LEAVE SUMMARY REQUEST : approved leave summary request.'),
        #                          'headings': _('WB B2B : APPROVED LEAVE SUMMARY REQUEST')}
        #     self.env['one.signal.notification.message'].create(one_signal_values)
            if employee.device_token and self.employee_id.approve_manager.id:
                content = 'LEAVE SUMMARY REQUEST: %s submitted leave summary request.' % self.employee_id.approve_manager.name
                message_title ='MAEX : SUBMITTED LEAVE SUMMARY REQUEST'
                firebase_values = {'employee_id': employee.id,
                                   'contents': content,
                                   'headings': message_title}
                self.env['firebase.notification.message'].create(firebase_values)
                employee.send_noti([employee.device_token], content, message_title)
            
    def _validate_leaves(self):
        if self.leave_line.filtered(lambda l: not l.full and not l.first and not l.second):
            return {'status': False, 'message': 'Please Choose which part of the day to request leave!'}
        # if self.holiday_status_id.allocation_type != 'no':
        #     mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
        #     leave_days = mapped_days[self.employee_id.id][self.holiday_status_id.id]
        #     no_of_leaves = self.duration
        #     if float_compare(leave_days['remaining_leaves'], no_of_leaves, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], no_of_leaves, precision_digits=2) == -1:
        #         return {'status': False, 'message': 'The number of remaining time off is not sufficient for this time off type. Please also check the time off waiting for validation.'}
        for line in self.leave_line:
            domain = [('date_from', '<', line.end_date), ('date_to', '>', line.start_date),
                      ('employee_id', '=', self.employee_id.id), ('state', 'not in', ('cancel', 'refuse'))]
            if self.env['hr.leave'].search(domain):
                return {'status': False, 'message': 'You can not set 2 times off that overlaps on the same day for the same employee.'}
        return {'status': True, 'message': 'Successfully Submitted!'}

    def action_submit(self):
        result = self._validate_leaves()
        if not result['status']:
            raise ValidationError(result['message'])
        self.state = 'submit'
        topic_name = "leave_summary_request"
        message_title = "MAEX : SUBMITTED LEAVE SUMMARY REQUEST"
        message_body = "LEAVE SUMMARY REQUEST: " + self.employee_id.name + " submitted leave summary request."
        if self.employee_id.device_token:
            firebase_values = {'employee_id': self.employee_id.id,
                               'contents': message_body,
                               'headings': message_title}
            self.env['firebase.notification.message'].create(firebase_values)
            self.employee_id.send_noti([self.employee_id.device_token], message_title, message_body)

        return result
    
    def _get_sunday_list(self,employee_id,date_from,date_to):
        end_date = date_to
        beg_date = date_from
        sunday_list = []
        sunday_count = 0
        
        while beg_date <= end_date:
            dayofweek = beg_date.weekday()
            public_holiday = self.env['public.holidays.line'].search([('date', '=', beg_date),'|',
                                                                      ('line_id.company_id', '=', employee_id.company_id.id), ('line_id.company_id', '=', False)], order='id desc', limit=1)
            # if employee_id.resource_calendar_id.no_holidays == True:
            #     dayofweek = 0
            
            if dayofweek == 6:
                sunday_count += 1
            elif public_holiday:
                sunday_count += 1
                     
            beg_date = beg_date + timedelta(days=1)            
        
        return sunday_count
    
    def button_submit(self):
        result = self._validate_leaves()
        if result['status']:
            self.state = 'submit'
            self._create_notification_message()
        return result

    def button_approve(self):
        for line in self.leave_line:
            resource_calendar = self.resource_calendar_id or self.employee_id.resource_calendar_id
            tz = timezone(resource_calendar.tz)
            leave_obj = self.env['hr.leave']
            no_of_days = 1 if line.full else 0.5
            request_unit_half = no_of_days == 0.5
            value = {'employee_id': self.employee_id.id,
                     'date_from': line.start_date,
                     'date_to': line.end_date,
                     'holiday_status_id': self.holiday_status_id.id,
                     'request_date_from': get_local_datetime(tz, line.start_date).date(),
                     'request_date_to': get_local_datetime(tz, line.end_date).date(),
                     'number_of_days': no_of_days,
                     'summary_request_id': self.id,
                     'name': self.description,
                     'request_unit_half': request_unit_half,
                     }
            leave = leave_obj.create(value)
            leave.action_approve()
            leave.action_validate()
            self._create_approved_notification_message(self.employee_id)
            self.state = 'approve'

    def button_cancel(self):
        # import pdb
        # pdb.set_trace()
        self.state = 'refuse'
        for leave in self.env['hr.leave'].search([('summary_request_id', '=', self.id),('state','in',('draft', 'confirm', 'validate', 'validate1'))]):
            leave.action_refuse()
        # one_signal_values = {'employee_id': self.employee_id.id,
        #                      'contents': _('LEAVE SUMMARY REQUEST : rejected leave summary request.'),
        #                      'headings': _('WB B2B : REJECTED LEAVE SUMMARY REQUEST')}
        # self.env['one.signal.notification.message'].create(one_signal_values)
        content = 'LEAVE SUMMARY REQUEST : rejected leave summary request.'
        message_title = 'MAEX : REJECTED LEAVE SUMMARY REQUEST'
        if self.employee_id.device_token:
            firebase_values = {'employee_id': self.employee_id.id,
                               'contents': content,
                               'headings': message_title}
            self.env['firebase.notification.message'].create(firebase_values)
            self.employee_id.send_noti([self.employee_id.device_token], content, message_title)

    # def button_verify(self):
    #     self.state = 'verify'

    def button_draft(self):
        self.state = 'draft'
        # for leave in self.env['hr.leave'].search([('summary_request_id', '=', self.id)]):
        #     leave.action_draft()
         
    @api.onchange('start_date', 'end_date', 'employee_id')
    def onchange_dates(self):
        if self.start_date and self.end_date and self.employee_id:
            if self.start_date > self.end_date:
                raise ValidationError(_('End Date should be greater than or equal to Start Date.'))
            self.resource_calendar_id = self.employee_id.contract_id and self.employee_id.contract_id.resource_calendar_id or self.employee_id.resource_calendar_id

            day_count = (self.end_date - self.start_date).days + 1
            leave_lines = self.env['summary.request.line']
            for single_date in (self.start_date + timedelta(n) for n in range(day_count)):                
                new_line_values = leave_lines.calculate_line_values(self.resource_calendar_id, single_date)
                for new_line_value in new_line_values:
                    distinct_shift = new_line_value['distinct_shift']
                    next_day_hour_id = new_line_value['next_day_hour_id']
                    this_day_hour_id = new_line_value['this_day_hour_id']
                    new_line_value.update(leave_lines._compute_allow_edit(single_date, self.start_date, self.end_date, next_day_hour_id, distinct_shift))
                    if this_day_hour_id:
                        resource_id = self.env['resource.calendar.attendance'].browse([this_day_hour_id])
                        if resource_id.hour_from == 18:
                            new_line_value.update({'allow_first_edit': True})
                    new_line = leave_lines.new(new_line_value)
                    leave_lines += new_line
            self.leave_line = leave_lines
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id
            
    @api.depends('leave_line.full', 'leave_line.first', 'leave_line.second')
    def compute_duration(self):
        for day in self:
            total_day = 0                
            for line in day.leave_line:
                if line.full:
                    total_day += 1
                elif line.first:
                    total_day += 0.5
                elif line.second:
                    total_day += 0.5
            day.duration = total_day
            sunday_count = 0
            if total_day > 1:
                sunday_count = self._get_sunday_list(day.employee_id,day.start_date,day.end_date)  
            day.unpaid_leave = sunday_count + total_day
            day.duration_unpaid_leave = sunday_count + total_day
            
    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].sudo().browse(vals['employee_id'])
        employee_name = employee.name
        leave_type = self.env['hr.leave.type'].sudo().browse(vals['holiday_status_id'])
        vals['name'] = employee_name + ' on ' + leave_type.name
        if not vals.get('resource_calendar_id'):
            vals['resource_calendar_id'] = employee.resource_calendar_id.id
        if 'casual' in leave_type.name.lower() or 'annual' in leave_type.name.lower():
            if leave_type.max_continuous_days > 0:
                duration = 0                
                if 'duration' in vals:
                    duration = vals['duration']
                else:
                    if 'leave_line' in vals:
                        for line in vals['leave_line']:
                            if line[2]['full'] == True:
                                duration += 1
                            elif line[2]['first'] == True:
                                duration += 0.5
                            elif line[2]['second'] == True:
                                duration += 0.5
                if duration > leave_type.max_continuous_days:
                    raise ValidationError(_('Cannot allow more than %s continuous days for %s!') % (leave_type.max_continuous_days, leave_type.name))
            if leave_type.pre_requested_days > 0:
                start_date = vals['start_date']
                pre_request_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=3)
                today = fields.Date.today()
                if today > pre_request_date:
                    raise ValidationError(_('You need to request at least %s days prior to the start date for %s!') % (leave_type.pre_requested_days, leave_type.name))
        return super(SummaryRequest, self).create(vals)

    def write(self, vals):
        employee_name = self.env['hr.employee'].browse(vals.get('employee_id', self.employee_id.id)).name
        leave_type_name = self.env['hr.leave.type'].browse(vals.get('holiday_status_id', self.holiday_status_id.id)).name
        vals['name'] = employee_name + ' on ' + leave_type_name
        return super(SummaryRequest, self).write(vals)

    @api.constrains('start_date', 'end_date', 'employee_id')
    def check_overlap_record(self):
        for req in self:
            if req.start_date and req.end_date and req.employee_id:
                result = req._validate_leaves()
                if not result['status']:
                    raise ValidationError(result['message'])

    def unlink(self):
        for req in self:

            if self.env.user.has_group('base.group_system'):
                for leave in self.env['hr.leave'].search([('summary_request_id', '=', req.id)]):
                    if req.state in ['approve']:
                        leave.action_refuse()

                    else:
                        #leave.action_darft()
                        leave.write({'summary_request_id':False,'state':'draft'})
                        leave.unlink()
            else:
                raise ValidationError(_("""You don't have access right to delete record! User group must have administration setting access rights"""))

        return super(SummaryRequest, self).unlink()


class LeaveLine(models.Model):
    _name = 'summary.request.line'   
 
    request_id = fields.Many2one('summary.request', string='Summary Request', index=True, required=True, ondelete='cascade')
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0')
    date = fields.Date(string='Date', required=True)
    full = fields.Boolean(string='Full', default=True)
    first = fields.Boolean(string='First Half', default=False)
    second = fields.Boolean(string='Second Half', default=False)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    this_day_hour_id = fields.Many2one('resource.calendar.attendance', string='This Day', required=True)
    next_day_hour_id = fields.Many2one('resource.calendar.attendance', string='Next Day')
    resource_calendar_id = fields.Many2one('resource.calendar')
    distinct_shift = fields.Selection([('whole', 'The Whole Day'), ('morning', 'Morning '), ('afternoon', 'Afternoon')], default='', copy=False)
    allow_full_edit = fields.Boolean('Allow Editing')
    allow_first_edit = fields.Boolean('Allow Editing')
    allow_second_edit = fields.Boolean('Allow Editing')

    def _compute_allow_edit(self, request_date, start_date, end_date, next_day_hour_id, distinct_shift=''):
        allow_full_edit = True
        allow_first_edit = True
        allow_second_edit = True
        if distinct_shift == 'afternoon':
            allow_first_edit = False
            allow_full_edit = False
        elif distinct_shift == 'morning':
            allow_second_edit = False
            allow_full_edit = False

        if start_date == end_date:
            if next_day_hour_id or distinct_shift == 'morning':
                allow_second_edit = False
                if next_day_hour_id:
                    resource_id = self.env['resource.calendar.attendance'].browse([next_day_hour_id])
                    if resource_id.hour_from == 0:
                        allow_second_edit = True
            else:
                allow_second_edit = True
        elif request_date == start_date:
            allow_first_edit = False
        elif request_date == end_date:
            allow_second_edit = False
        else:
            allow_full_edit = False
            allow_first_edit = False
            allow_second_edit = False
        
        return {'allow_full_edit': allow_full_edit, 'allow_first_edit': allow_first_edit, 'allow_second_edit': allow_second_edit}

    def _get_domain(self, resource_calendar, date):
        domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', resource_calendar.id),
                  ('dayofweek', '=', str(date.weekday()))]
        if resource_calendar.two_weeks_calendar:
            week_type = int(math.floor((date.toordinal() - 1) / 7) % 2)
            domain += [('week_type', '=', str(week_type))]
        return domain

    def calculate_line_values(self, resource_calendar, date):
        value_lines = []
        # public_holiday = self.env['public.holidays.line'].search([])
        public_holiday = self.env['public.holidays.line'].search([('date', '=', date), ('type', '=', 'holiday')])

        if public_holiday:
            return value_lines
        calendar_obj = self.env['resource.calendar.attendance']
        dayofweek = str(date.weekday())
        tz = timezone(resource_calendar.tz)
        domain = self._get_domain(resource_calendar, date)

        working_hours = calendar_obj.search(domain)
        for hour in working_hours:
            if round(hour.hour_from) == 0:
                continue
            elif round(hour.hour_to) == 24:
                local_start_date = datetime.combine(fields.Datetime.to_datetime(date), float_to_time(hour.hour_from))
 
                next_date = date + timedelta(days=1)
                next_domain = self._get_domain(resource_calendar, next_date)
                next_hour = calendar_obj.search(next_domain).filtered(lambda h: round(h.hour_from) == 0)
 
                local_end_date = datetime.combine(fields.Datetime.to_datetime(next_date), float_to_time(next_hour.hour_to))
 
                start_date = datetime.strftime(get_utc_datetime(tz, local_start_date), DT_FORMAT)
                end_date = datetime.strftime(get_utc_datetime(tz, local_end_date), DT_FORMAT)
                value_lines.append({'dayofweek': dayofweek,
                                    'date': date,
                                    'distinct_shift': '',
                                    'full': True,
                                    'first': False,
                                    'second': False,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'this_day_hour_id': hour.id,
                                    'next_day_hour_id': next_hour.id,
                                    'resource_calendar_id': resource_calendar.id, })
            else:
                local_start_date = datetime.combine(fields.Datetime.to_datetime(date), float_to_time(hour.hour_from))
                local_end_date = datetime.combine(fields.Datetime.to_datetime(date), float_to_time(hour.hour_to))
                start_date = datetime.strftime(get_utc_datetime(tz, local_start_date), DT_FORMAT)
                end_date = datetime.strftime(get_utc_datetime(tz, local_end_date), DT_FORMAT)
                value = {'dayofweek': dayofweek,
                         'date': date,
                         'start_date': start_date,
                         'end_date': end_date,
                         'this_day_hour_id': hour.id,
                         'next_day_hour_id': 0,
                         'resource_calendar_id': resource_calendar.id}
                if working_hours.filtered(lambda h: round(h.hour_from) == 0):
                    value.update({'distinct_shift': 'afternoon', 'second': True, 'first': False, 'full': False})
                elif working_hours.filtered(lambda h: round(h.hour_to) == 24):
                    value.update({'distinct_shift': 'morning', 'first': True, 'second': False, 'full': False})
                else:
                    value.update({'distinct_shift': 'whole', 'full': True, 'second': False, 'first': False})
                value_lines.append(value)
        return value_lines

    @api.onchange('full', 'first', 'second')
    def onchange_leave_options(self):
        if self.resource_calendar_id:
            start_date, end_date = self.manipulate_options(self.date, self.this_day_hour_id.id, self.next_day_hour_id.id, self.distinct_shift, self.first, self.second)
            self.start_date = datetime.strftime(start_date, DT_FORMAT)
            self.end_date = datetime.strftime(end_date, DT_FORMAT)

    def manipulate_options(self, request_date, this_day_hour_id, next_day_hour_id, distinct_shift, first, second):
        rca_obj = self.env['resource.calendar.attendance']
        this_day_hour = rca_obj.browse(this_day_hour_id)
        next_day_hour = rca_obj.browse(next_day_hour_id) if next_day_hour_id else False
        from_date = to_date = request_date
        next_day = request_date + timedelta(days=1)
        tz = timezone(this_day_hour.calendar_id.tz)

        if not distinct_shift or distinct_shift == '':
            if first:
                hour_from = this_day_hour.hour_from
                hour_to = this_day_hour.hour_to
            elif second:
                hour_from = next_day_hour.hour_from
                hour_to = next_day_hour.hour_to
                from_date = to_date = next_day
            else:
                hour_from = this_day_hour.hour_from
                if next_day_hour:
                    hour_to = next_day_hour.hour_to
                    to_date = next_day
                else:
                    hour_to = this_day_hour.hour_to
                
        elif distinct_shift == 'whole':
            hours = this_day_hour
            half_day = (hours.hour_from + hours.hour_to) / 2
            if first:
                hour_from = hours.hour_from
                hour_to = half_day
            elif second:
                hour_from = half_day
                hour_to = hours.hour_to
            else:
                hour_from = this_day_hour.hour_from
                hour_to = this_day_hour.hour_to
        else:
            hour_from = this_day_hour.hour_from
            hour_to = this_day_hour.hour_to

        local_start_date = datetime.combine(fields.Datetime.to_datetime(from_date), float_to_time(hour_from))
        local_end_date = datetime.combine(fields.Datetime.to_datetime(to_date), float_to_time(hour_to))
        if self._context.get('via') and self._context.get('via') == 'mobile':
            return local_start_date, local_end_date
        start_date = get_utc_datetime(tz, local_start_date)
        end_date = get_utc_datetime(tz, local_end_date)
        return start_date, end_date

class Employee(models.Model):
    _inherit = 'hr.employee'

    def send_noti(self,registration_ids, message_title, message_body):
        fcm_api_key = self.env['ir.config_parameter'].sudo().get_param('fcm_api_key')
        if fcm_api_key:
            push_service = FCMNotification(api_key=fcm_api_key)
            result = push_service.notify_multiple_devices(registration_ids=registration_ids,
                                                          message_body=message_body, message_title=message_title,
                                                          tag=None)
