# -*- coding: utf-8 -*-
import logging
import math
import json
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from pytz import timezone, UTC
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo.tools import format_datetime, DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
from odoo.addons.hr_attendance_ext.models.hr_attendance import time_to_float
import time


_logger = logging.getLogger(__name__)


def get_utc_datetime(tz, local_dt_str):
    local_datetime = datetime.strptime(local_dt_str, DT_FORMAT)
    utc_datetime = tz.localize(local_datetime.replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
    return utc_datetime.strftime(DT_FORMAT)


def get_local_date(tz, utc_datetime):
    local_datetime = UTC.localize(utc_datetime.replace(tzinfo=None), is_dst=True).astimezone(tz=tz)
    return local_datetime.strftime('%d/%m/%Y')


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    missed = fields.Boolean(string='Missed', default=False, copy=False)


class HrAttendanceRaw(models.Model):
    _name = 'hr.attendance.raw'
    _description = 'Attendance Raw Data'
    _order = 'create_date desc'
    
    # def get_lat_lng(self):
    #     json_map = 'https://maps.google.com/?q=20.593684,78.96288'
    #     return json_map
    #

    
    name = fields.Char(string='Name', readonly=True)
    fingerprint_id = fields.Char(string='Fingerprint ID', required=True)
    employee_name = fields.Char('Employee Name')
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon')], 'Day Period', compute='_compute_period')
    date = fields.Date('Date', compute='_compute_period')
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, compute='_compute_period')
    week_type = fields.Selection([
        ('1', 'Odd week'),
        ('0', 'Even week')
    ], 'Week Even/Odd', compute='_compute_period')
    attendance_datetime = fields.Datetime('Attendance Datetime', required=True)
    float_time = fields.Float('Time', compute='_compute_period')
    imported = fields.Boolean(string='Imported', default=False, copy=False)
    source = fields.Char(string='Source')
    negligible = fields.Boolean('Negligible', default=False, copy=False)
    company = fields.Char(string='Company', required=False)
    branch = fields.Char(string='Branch')
    action = fields.Selection([('check_in', 'Check in'), ('check_out', 'Check out')], string='Action', copy=False)
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    
    google_map_partner = fields.Char(string="Map Link",compute='_compute_lat_lng')
    
    @api.depends('latitude','longitude')
    def _compute_lat_lng(self):
        for att in self:
            if att.latitude and att.longitude:
                lat_lng  = str(att.latitude) + ',' + str(att.longitude)
                json_map = 'https://maps.google.com/?q=' + lat_lng
            else:
                json_map = ''
                
            att.google_map_partner = json_map
    
    
    def go_map(self):
        result =  {
                  'name'     : 'Go to Map',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
               }
        result['url'] = self.google_map_partner
            
        return result
    
    
    @api.depends('attendance_datetime')
    def _compute_period(self):
        for raw in self:
            raw.date = False
            raw.day_period = False
            raw.dayofweek = False
            raw.week_type = False
            raw.float_time = False
            if raw.fingerprint_id and raw.attendance_datetime:
                employee = self.env['hr.employee'].search([('fingerprint_id', '=', raw.fingerprint_id)])
                calendar = employee.resource_calendar_id
                if calendar:
                    tz = timezone(employee.tz or calendar.tz)
                    local_dt = raw.attendance_datetime.astimezone(tz)
                    dt_float = time_to_float(local_dt)
                    raw.date = local_dt.date()
                    raw.day_period = dt_float < 12 and 'morning' or 'afternoon'
                    raw.dayofweek = str(raw.date.weekday())
                    raw.week_type = str(int(math.floor((raw.date.toordinal() - 1) / 7) % 2))
                    raw.float_time = dt_float

    @api.onchange('fingerprint_id')
    def onchange_fingerprint_id(self):
        if self.fingerprint_id :
            
            employee = self.env['hr.employee'].search([('fingerprint_id', '=', self.fingerprint_id)])
            if not employee:
                raise ValidationError(_("Fingerprint ID %s is not found") % self.fingerprint_id)
            if not self.employee_name:
                self.employee_name = employee.name
            
#         if self.fingerprint_id and self.company:
#             company = self.env['res.company'].search([('name', '=', self.company)])
#             if company:
#                 employee = self.env['hr.employee'].search([('fingerprint_id', '=', self.fingerprint_id), ('company_id', '=', company.id)])
#                 if not employee:
#                     raise ValidationError(_("Fingerprint ID %s is not found") % self.fingerprint_id)
#                 if not self.employee_name:
#                     self.employee_name = employee.name
#             else:
#                 raise ValidationError(_("Company Name '%s' is not found") % self.company)

    @api.model
    def create(self, vals):
        if vals:
            if vals.get('employee_id') :
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                vals['company'] = employee.company_id.name
                # vals['branch'] = employee.branch_id.name
                vals.pop('employee_id')
            elif vals.get('fingerprint_id'):
                employee = self.env['hr.employee'].search([('fingerprint_id', '=', vals.get('fingerprint_id'))])
                vals['company'] = employee.company_id.name
                # vals['branch'] = employee.branch_id.name
            else:
                company = self.env['res.company'].search([('name', '=', vals['company'])])
                if not company:
                    raise ValidationError(_("Company Name '%s' is not found") % vals['company'])
                employee = self.env['hr.employee'].search([('fingerprint_id', '=', vals['fingerprint_id'])])
                if not employee:
                    raise ValidationError(_("Fingerprint ID %s is not found") % vals['fingerprint_id'])
            if not vals.get('employee_name'):
                vals['employee_name'] = employee.name

            calendar = employee.contract_id and employee.contract_id.resource_calendar_id or employee.resource_calendar_id
            tz = timezone(calendar.tz or 'Asia/Yangon')
            if not self._context.get('from_web_view'):
                vals['attendance_datetime'] = get_utc_datetime(tz, vals.get('attendance_datetime'))
            result = super(HrAttendanceRaw, self).create(vals)
            result.name = result.employee_name + ' - ' + get_local_date(tz, result.attendance_datetime)
            return result

    @api.onchange('fingerprint_id', 'company', 'attendance_datetime')
    def _check_duplicate(self):
        for record in self:
            if record.fingerprint_id and record.company and record.attendance_datetime:
                if self.search([('fingerprint_id', '=', record.fingerprint_id), ('company', '=', record.company),
                                ('attendance_datetime', '=', record.attendance_datetime), ('id', '!=', record.id)]):
                    raise ValidationError(_("Duplicate record found!" ))
    
    def check_exit_or_not_shift(self,date_start,date_stop,employee,value):
        attendance_obj = self.env['hr.attendance'].sudo()
        night_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                     ('check_out', '=', date_stop),
                                                     ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
        if night_shift:
            night_shift.night_shift.write(value)
            return False
        
        distinct_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                            ('check_in', '<', date_stop),
                                                            ('employee_id', '=', employee.id)], order='check_in asc', limit=1)
        if distinct_shift:
            distinct_shift.write(value)
            return False
        return True
    
    def check_distinct_workhour(self,att):
        calendar = att.employee_id.resource_calendar_id
        tz = timezone(calendar.tz)
        check_in = att.check_in + timedelta(hours=+6,minutes=+30)#att.check_in.astimezone(tz)
        
        in_float = time_to_float(check_in)
        start_time_early = math.floor(in_float - 2) 
        start_time_late = math.floor(in_float + 2)        
        dayofweek = check_in.weekday()                
        day_period = in_float < 12 and 'morning' or 'afternoon'

        domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id),
                  ('dayofweek', '=', str(dayofweek)), ('day_period', '=', day_period)]
        if calendar.two_weeks_calendar:
            week_type = int(math.floor((check_in.toordinal() - 1) / 7) % 2)
            domain += [('week_type', '=', str(week_type))]

        working_hours = self.env['resource.calendar.attendance'].search(domain)
        result = 2
        hour_exist = False
        for wh in working_hours:
            hour_from = wh.hour_from + 0.000001
            hour_to = wh.hour_to + 0.000001
            in_diff = out_diff = 0
            if start_time_early < math.floor(wh.hour_from) < start_time_late:                
                worked_hour = int(math.ceil(hour_to - hour_from))#math.floor(hour_to - hour_from)
                hour_exist = True
        if hour_exist == True:    
            early_out = worked_hour - 2.5
            late_out = worked_hour + 2.5
        else:
            early_out = 0
            late_out = 0
        early_out_time = att.check_in + timedelta(hours=+early_out)
        late_out_time = att.check_in + timedelta(hours=+late_out) 
        return late_out_time
            
    def import_attendances(self):
        domain = [('imported', '=', False)]
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]
        self = self.search(domain, order='attendance_datetime asc')
        if len(self) == 0:
            _logger.info(_("No attendance raw left to import!"))

        attendance_obj = self.env['hr.attendance'].sudo()
        for raw in self:
            
            # import pdb
            # pdb.set_trace()
            
            employee = self.env['hr.employee'].search([('fingerprint_id', '=', raw.fingerprint_id)])
            if not employee:
                continue
            calendar = employee.contract_id and employee.contract_id.resource_calendar_id or employee.resource_calendar_id
            tz = timezone(employee.tz or calendar.tz or 'Asia/Yangon')
            raw_local = raw.attendance_datetime.astimezone(tz)
            raw_float_time = time_to_float(raw.attendance_datetime + timedelta(hours=+6, minutes=+30))
            raw_day_period = raw_float_time < 12 and 'morning' or 'afternoon'
            #datetime_obj = datetime.strptime(raw_local, "%Y-%m-%d %H:%M:%S")
            if not employee.resource_calendar_id.is_roaster:
                if (calendar.two_weeks_calendar and raw_day_period =='morning') or (employee.resource_calendar_id.hours_per_day > 10 and raw_day_period =='morning'):
                    self.env.cr.execute("""select (
                    select %s::timestamp without time zone + interval '5 hours 15 minutes')::date as raw_date""",(raw_local,))
                    result = self.env.cr.dictfetchall()[0]
                    datetime_obj_utc = raw_local.replace(tzinfo=tz).date()
                    raw_date = raw_local.date()
                    raw_date = result['raw_date']
                elif raw_day_period =='morning':
                    self.env.cr.execute("""select (
                    select %s::timestamp without time zone + interval '6 hours 30 minutes')::date as raw_date""",(raw_local,))
                    
                    result = self.env.cr.dictfetchall()[0]
                    datetime_obj_utc = raw_local.replace(tzinfo=tz).date()
                    raw_date = raw_local.date()
                    raw_date = result['raw_date']
                else:
                    raw_date = raw_local.date()

                raw_float_time = time_to_float(raw.attendance_datetime + timedelta(hours=+6,minutes=+30))            
                raw_day_period = raw_float_time < 12 and 'morning' or 'afternoon'
                date_start = tz.localize((fields.Datetime.to_datetime(raw_date)), is_dst=True).astimezone(tz=UTC)
                date_stop = tz.localize((datetime.combine(fields.Datetime.to_datetime(raw_date), datetime.max.time())), is_dst=True).astimezone(tz=UTC)

                dayofweek = raw_date.weekday()
                domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id), ('dayofweek', '=', str(dayofweek))]
                if calendar.two_weeks_calendar:
                    week_type = int(math.floor((raw_date.toordinal() - 1) / 7) % 2)
                    domain += [('week_type', '=', str(week_type))]

                working_hours = self.env['resource.calendar.attendance'].search(domain)

                if len(working_hours) == 2:
                    day_start = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                    day_stop = datetime.strftime(date_stop, '%Y-%m-%d %H:%M:%S')
                    att_value = {}
                    night_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                        ('check_out', '=', date_stop),
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)

                    if not working_hours.filtered(lambda wh: wh.start_end == 'end'):
                        distinct_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                                ('check_in', '<', date_stop),
                                                                ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                        try:
                            if distinct_shift and night_shift:
                                if distinct_shift.check_out:
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_shift.check_in = raw.attendance_datetime
                                else:
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        if distinct_shift.check_in > night_shift.check_in:
                                            night_check_in = distinct_shift.check_in
                                            distinct_check_out = night_shift.check_in
                                            night_shift.check_in = night_check_in
                                            distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out})
                                        else:
                                            check_out_time = distinct_shift.check_in
                                            distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': check_out_time})
                                    elif night_shift.check_in < raw.attendance_datetime:
                                        distinct_check_out = night_shift.check_in
                                        night_shift.check_in = raw.attendance_datetime
                                        distinct_shift.check_out = distinct_check_out
                                    else:
                                        distinct_shift.check_out = raw.attendance_datetime

                            elif distinct_shift:
                                if distinct_shift.check_out:
                                    distinct_date_and_time = distinct_shift.check_out + timedelta(hours = 1)
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_check_out = distinct_shift.check_in
                                        night_check_in = distinct_shift.check_out
                                        distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out})
                                        att_value.update({'employee_id': employee.id, 'check_in': night_check_in, 'check_out': day_stop})
                                    # elif  distinct_shift.check_in < raw.attendance_datetime <= distinct_date_and_time:
                                    #     distinct_shift.write({'check_out': raw.attendance_datetime})
                                    elif distinct_shift.check_out < raw.attendance_datetime:
                                        #att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop,'missed':True})
                                        att_date = raw.attendance_datetime + timedelta(hours=+6)
                                        print(att_date.hour,att_date)
                                        if 16 <= att_date.hour <= 18:
                                            att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out': day_stop})
                                        else:
                                            att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                    else:
                                        night_check_in = distinct_shift.check_out
                                        distinct_shift.check_out = raw.attendance_datetime
                                        att_value.update({'employee_id': employee.id, 'check_in': night_check_in, 'check_out': day_stop})
                                else:
                                    distinct_date_check_in = distinct_shift.check_in + timedelta(hours = 1)
                                    distinct_late_out = self.check_distinct_workhour(distinct_shift)
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_check_out = distinct_shift.check_in
                                        distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out,'missed':False})
                                    elif raw.attendance_datetime <= distinct_date_check_in:
                                        raw.imported = True
                                        self._cr.commit()
                                        continue
                                    elif raw.attendance_datetime > distinct_late_out:
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out': day_stop})
                                        raw.imported = True
                                        self._cr.commit()
                                        continue
                                    else:
                                        distinct_shift.check_out = raw.attendance_datetime
                                        distinct_shift.missed = False
                            elif night_shift:
                                if night_shift.check_in > raw.attendance_datetime:
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                else:
                                    distinct_check_in = night_shift.check_in
                                    night_shift.check_in = raw.attendance_datetime
                                    att_value.update({'employee_id': employee.id, 'check_in': distinct_check_in,'missed':True})
                            else:
                                #att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                if raw_day_period == 'afternoon':
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                                else:
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
    #                             if raw_day_period == 'morning':
    #                                 att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
    #                             else:
    #                                 att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                            if att_value:                            
                                hr_att_id = attendance_obj.create(att_value)
                        except ValidationError as e:
                            _logger.error(e.name)
                    else:
                        distinct_hour = working_hours.filtered(lambda wh: wh.start_end == 'start' and round(wh.hour_to) < 24)
                        morning_hour = working_hours.filtered(lambda wh: wh.start_end == 'end')
                        avg = 0
                        if distinct_hour:
                            avg = (morning_hour.hour_to + distinct_hour.hour_from) / 2
                            night_shift = attendance_obj.search([('check_in', '>', date_start),
                                                                ('check_in', '<', date_stop),
                                                                ('employee_id', '=', employee.id)],
                                                                order='check_in desc', limit=1)
                        morning_shift = attendance_obj.search([('check_in', '=', date_start),
                                                           ('check_out', '<=', date_stop),
                                                           ('employee_id', '=', employee.id)],
                                                          order='check_in desc', limit=1)
                        try:
                            if morning_shift and night_shift:
                                if distinct_hour:
                                    if night_shift.check_out:
                                        if night_shift.check_out < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        elif night_shift.check_in > raw.attendance_datetime > morning_shift.check_out:
                                            if avg > raw_float_time:
                                                morning_shift.check_out = raw.attendance_datetime
                                            else:
                                                night_shift.check_in = raw.attendance_datetime
                                        elif night_shift.check_in < raw.attendance_datetime:
                                            if avg < time_to_float(night_shift.check_in.astimezone(tz)):
                                                morning_check_out = night_shift.check_in
                                                morning_shift.check_out = morning_check_out
                                                night_shift.check_in = raw.attendance_datetime
                                    else:
                                        if night_shift.check_in < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        elif morning_shift.check_out < raw.attendance_datetime < night_shift.check_in:
                                            night_check_out = night_shift.check_in
                                            night_shift.write({'check_in': raw.attendance_datetime, 'check_out': night_check_out})
                                        else:
                                            night_check_in = morning_shift.check_out
                                            night_check_out = night_shift.check_in
                                            morning_shift.check_out = raw.attendance_datetime
                                            night_shift.write({'check_in': night_check_in, 'check_out': night_check_out})
                                else:
                                    if morning_shift.check_out < raw.attendance_datetime < night_shift.check_in:
                                        if raw_day_period == 'morning':
                                            morning_shift.check_out = raw.attendance_datetime
                                        else:
                                            night_shift.check_in = raw.attendance_datetime
                            elif morning_shift:
                                
                                morning_in = morning_shift.check_out + timedelta(hours=+1)
                                if morning_shift.check_out > raw.attendance_datetime:
                                    att_value.update({'employee_id': employee.id, 'check_in': morning_shift.check_out})
                                    morning_shift.check_out = raw.attendance_datetime
                                elif morning_shift.check_out < raw.attendance_datetime <= morning_in:
                                    continue
                                else:
                                    check_in_exit = attendance_obj.search([('check_in', '<', raw.attendance_datetime),
                                                        ('check_out', '=', day_stop),#                                                     
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                                    if check_in_exit:
                                        raw.imported = True
                                        continue
                                
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
                                if not distinct_hour:
                                    att_value.update({'check_out': day_stop})

                            elif night_shift:
                                if distinct_hour:
                                    if night_shift.check_out:
                                        if raw.attendance_datetime < night_shift.check_in:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                        elif night_shift.check_in < raw.attendance_datetime < night_shift.check_out:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                            night_shift.check_in = raw.attendance_datetime
                                        else:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                            night_check_in = night_shift.check_out
                                            night_shift.write({'check_in': night_check_in, 'check_out': raw.attendance_datetime})
                                    else:
                                        if night_shift.check_in < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        else:
                                            if avg < raw_float_time:
                                                night_check_out = night_shift.check_out
                                                night_shift.write({'check_in': raw.attendance_datetime, 'check_out': night_check_out})
                                            else:
                                                att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                else:
                                    if night_shift.check_in < raw.attendance_datetime:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                        night_shift.check_in = raw.attendance_datetime
                                    else:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                            else:
                                if distinct_hour:
                                    if avg < raw_float_time:
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
                                    else:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                else:
                                    if raw_day_period == 'morning':
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                    else:
                                        check_in_exit = attendance_obj.search([('check_in', '<', raw.attendance_datetime),
                                                        ('check_out', '=', day_stop),#                                                     
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                                        if check_in_exit:
                                            raw.imported = True
                                            continue
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                            if att_value:
                                att_id = attendance_obj.create(att_value)
                                raw.imported = True            
                                self._cr.commit()
                        except ValidationError as e:
                            _logger.error(e.name)
                else:
                                                
                    attendance = attendance_obj.search([('check_in', '>=', date_start),
                                                        ('check_in', '<', date_stop),
    #                                                     ('check_in','>=',str(raw_date)+ ' 00:00:00'),
    #                                                     ('check_in', '<', str(raw_date)+ ' 23:59:59'),
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)

                    if attendance :
                        update_value = {}
                        try:
                            if attendance.check_out:
                                if attendance.check_in > raw.attendance_datetime:
                                    update_value.update({'check_in': raw.attendance_datetime})
                                elif attendance.check_out < raw.attendance_datetime :
                                    if attendance.check_out.date() == raw.attendance_datetime.date():                                    
                                        update_value.update({'check_out': raw.attendance_datetime})
                                    else:
                                        hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                        
                                else:
                                    raw.negligible = True
                                    _logger.info(_("This raw attendance datetime %s for %s is Negligible"),
                                    format_datetime(self.env, raw.attendance_datetime, dt_format=False), raw.employee_name)
                            else:
                                print("future_datereturn True_and_time>>")
                                future_date_and_time = attendance.check_in + timedelta(hours = 2)
                                print(attendance.id,">>>",attendance.check_in+ timedelta(hours=+6,minutes=+30))
                                if attendance.check_in > raw.attendance_datetime:
                                    check_out = attendance.check_in
                                    update_value.update({'check_in': raw.attendance_datetime, 'check_out': check_out})                            
                                elif future_date_and_time < raw.attendance_datetime:
                                    update_value.update({'check_out': raw.attendance_datetime})
                                else:
                                    raw.imported = True
                                    self._cr.commit()
                                    continue
                                #update_value.update({'check_out': raw.attendance_datetime})

                            updated = attendance.write(update_value)
                            if update_value:
                                if attendance.missed:
                                    attendance.missed = False
                                    raw.imported = True            
                                    self._cr.commit()
                        except ValidationError as e:
                            attendance.missed = True
                            _logger.error(e.name)
                    else:
                        try:
                            day_start = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                            day_stop = datetime.strftime(date_stop, '%Y-%m-%d %H:%M:%S')
                            # morning_hour = working_hours.filtered(lambda wh: wh.start_end in ['start','end'] and round(wh.hour_to) < 7)
                            # night_hour = working_hours.filtered(lambda wh: wh.start_end in ['start','end'] and round(wh.hour_to) == 24)
                            # att_date = raw.attendance_datetime + timedelta(hours=+6,minutes=+30)
                            # if morning_hour and att_date.hour > 1 and att_date.hour <= 7:
                            #     hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': day_start,'check_out':raw.attendance_datetime})
                                
                            # elif night_hour:
                            #     hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out':day_stop})
                                
                            # else:
                            hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                
                        except ValidationError as e:
                            last_attendance = attendance_obj.search([('employee_id', '=', employee.id),
                                                                    ('check_in', '=', raw.attendance_datetime)], order='id desc', limit=1)
                            
                
                            no_check_out_attendance = self.env['hr.attendance'].search([('employee_id', '=', employee.id),
                                                                                        ('check_out', '=', False),
                                                                                        ('id', '!=', last_attendance.id),
                                                                                        ], order='check_in desc', limit=1)
                            if no_check_out_attendance:
                                no_check_out_attendance.missed = True
                                raw.imported = True            
                                self._cr.commit()
                            _logger.error(e.name)
                raw.imported = True            
                self._cr.commit()
            
            elif employee.resource_calendar_id.is_roaster:
                if raw_day_period =='morning':
                    self.env.cr.execute("""select (
                    select %s::timestamp without time zone + interval '6 hours 30 minutes')::date as raw_date""",(raw_local,))
                    
                    result = self.env.cr.dictfetchall()[0]
                    datetime_obj_utc = raw_local.replace(tzinfo=tz).date()
                    raw_date = raw_local.date()
                    raw_date = result['raw_date']
                else:
                    raw_date = raw_local.date()
                    
                raw_float_time = time_to_float(raw.attendance_datetime + timedelta(hours=+6,minutes=+30))            
                raw_day_period = raw_float_time < 12 and 'morning' or 'afternoon'
                date_start = tz.localize((fields.Datetime.to_datetime(raw_date)), is_dst=True).astimezone(tz=UTC)
                date_stop = tz.localize((datetime.combine(fields.Datetime.to_datetime(raw_date), datetime.max.time())), is_dst=True).astimezone(tz=UTC)

                dayofweek = raw_date.weekday()                
                
                day_start = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                day_stop = datetime.strftime(date_stop, '%Y-%m-%d %H:%M:%S')
                domain = [('employee_id.name','=', raw.employee_name),('worked_day','=','true'),('state','=','approve'),('check_in','>=',day_start),('check_in', '<', day_stop)]
                duty_roaster = self.env['duty.roaster'].search(domain)
                if len(duty_roaster)==2:
                    cal_domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id), ('dayofweek', '=', str(raw_date.weekday()))]
                    if calendar.two_weeks_calendar:
                        week_type = int(math.floor((raw_date.toordinal() - 1) / 7) % 2)
                        cal_domain += [('week_type', '=', str(week_type))]
                    working_hours = self.env['resource.calendar.attendance'].search(cal_domain)
                    
                    day_start = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                    day_stop = datetime.strftime(date_stop, '%Y-%m-%d %H:%M:%S')
                    att_value = {}
                    night_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                        ('check_out', '=', date_stop),
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)

                    if not working_hours.filtered(lambda wh: wh.start_end == 'end'):
                        distinct_shift = attendance_obj.search([('check_in', '>=', date_start),
                                                                ('check_in', '<', date_stop),
                                                                ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                        try:
                            if distinct_shift and night_shift:
                                if distinct_shift.check_out:
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_shift.check_in = raw.attendance_datetime
                                else:
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        if distinct_shift.check_in > night_shift.check_in:
                                            night_check_in = distinct_shift.check_in
                                            distinct_check_out = night_shift.check_in
                                            night_shift.check_in = night_check_in
                                            distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out})
                                        else:
                                            check_out_time = distinct_shift.check_in
                                            distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': check_out_time})
                                    elif night_shift.check_in < raw.attendance_datetime:
                                        distinct_check_out = night_shift.check_in
                                        night_shift.check_in = raw.attendance_datetime
                                        distinct_shift.check_out = distinct_check_out
                                    else:
                                        distinct_shift.check_out = raw.attendance_datetime

                            elif distinct_shift:
                                if distinct_shift.check_out:
                                    distinct_date_and_time = distinct_shift.check_out + timedelta(hours = 1)
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_check_out = distinct_shift.check_in
                                        night_check_in = distinct_shift.check_out
                                        distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out})
                                        att_value.update({'employee_id': employee.id, 'check_in': night_check_in, 'check_out': day_stop})
                                    # elif  distinct_shift.check_in < raw.attendance_datetime <= distinct_date_and_time:
                                    #     distinct_shift.write({'check_out': raw.attendance_datetime})
                                    elif distinct_shift.check_out < raw.attendance_datetime:
                                        #att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop,'missed':True})
                                        att_date = raw.attendance_datetime + timedelta(hours=+6)
                                        print(att_date.hour,att_date)
                                        if 16 <= att_date.hour <= 18:
                                            att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out': day_stop})
                                        
                                        else:
                                            att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                    else:
                                        night_check_in = distinct_shift.check_out
                                        distinct_shift.check_out = raw.attendance_datetime
                                        att_value.update({'employee_id': employee.id, 'check_in': night_check_in, 'check_out': day_stop})
                                else:
                                    distinct_date_check_in = distinct_shift.check_in + timedelta(hours = 1)
                                    distinct_late_out = self.check_distinct_workhour(distinct_shift)
                                    if distinct_shift.check_in > raw.attendance_datetime:
                                        distinct_check_out = distinct_shift.check_in
                                        distinct_shift.write({'check_in': raw.attendance_datetime, 'check_out': distinct_check_out,'missed':False})
                                    elif raw.attendance_datetime <= distinct_date_check_in:
                                        raw.imported = True
                                        self._cr.commit()
                                        continue
                                    elif raw.attendance_datetime > distinct_late_out:
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out': day_stop})
                                        raw.imported = True
                                        self._cr.commit()
                                        continue
                                    else:
                                        distinct_shift.check_out = raw.attendance_datetime
                                        distinct_shift.missed = False
                            elif night_shift:
                                if night_shift.check_in > raw.attendance_datetime:
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                else:
                                    distinct_check_in = night_shift.check_in
                                    night_shift.check_in = raw.attendance_datetime
                                    att_value.update({'employee_id': employee.id, 'check_in': distinct_check_in,'missed':True})
                            else:
                                #att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                if raw_day_period == 'afternoon':
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                                else:
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
    #                             if raw_day_period == 'morning':
    #                                 att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
    #                             else:
    #                                 att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                            if att_value:                            
                                hr_att_id = attendance_obj.create(att_value)
                        except ValidationError as e:
                            _logger.error(e.name)
                    else:
                        distinct_hour = working_hours.filtered(lambda wh: wh.start_end == 'start' and round(wh.hour_to) < 24)
                        morning_hour = working_hours.filtered(lambda wh: wh.start_end == 'end')
                        avg = 0
                        if distinct_hour:
                            avg = (morning_hour.hour_to + distinct_hour.hour_from) / 2
                            night_shift = attendance_obj.search([('check_in', '>', date_start),
                                                                ('check_in', '<', date_stop),
                                                                ('employee_id', '=', employee.id)],
                                                                order='check_in desc', limit=1)
                        morning_shift = attendance_obj.search([('check_in', '=', date_start),
                                                           ('check_out', '<=', date_stop),
                                                           ('employee_id', '=', employee.id)],
                                                          order='check_in desc', limit=1)
                        try:
                            if morning_shift and night_shift:
                                if distinct_hour:
                                    if night_shift.check_out:
                                        if night_shift.check_out < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        elif night_shift.check_in > raw.attendance_datetime > morning_shift.check_out:
                                            if avg > raw_float_time:
                                                morning_shift.check_out = raw.attendance_datetime
                                            else:
                                                night_shift.check_in = raw.attendance_datetime
                                        elif night_shift.check_in < raw.attendance_datetime:
                                            if avg < time_to_float(night_shift.check_in.astimezone(tz)):
                                                morning_check_out = night_shift.check_in
                                                morning_shift.check_out = morning_check_out
                                                night_shift.check_in = raw.attendance_datetime
                                    else:
                                        if night_shift.check_in < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        elif morning_shift.check_out < raw.attendance_datetime < night_shift.check_in:
                                            night_check_out = night_shift.check_in
                                            night_shift.write({'check_in': raw.attendance_datetime, 'check_out': night_check_out})
                                        else:
                                            night_check_in = morning_shift.check_out
                                            night_check_out = night_shift.check_in
                                            morning_shift.check_out = raw.attendance_datetime
                                            night_shift.write({'check_in': night_check_in, 'check_out': night_check_out})
                                else:
                                    if morning_shift.check_out < raw.attendance_datetime < night_shift.check_in:
                                        if raw_day_period == 'morning':
                                            morning_shift.check_out = raw.attendance_datetime
                                        else:
                                            night_shift.check_in = raw.attendance_datetime
                            elif morning_shift:
                                
                                morning_in = morning_shift.check_out + timedelta(hours=+1)
                                if morning_shift.check_out > raw.attendance_datetime:
                                    att_value.update({'employee_id': employee.id, 'check_in': morning_shift.check_out})
                                    morning_shift.check_out = raw.attendance_datetime
                                elif morning_shift.check_out < raw.attendance_datetime <= morning_in:
                                    continue
                                else:
                                    check_in_exit = attendance_obj.search([('check_in', '<', raw.attendance_datetime),
                                                        ('check_out', '=', day_stop),#                                                     
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                                    if check_in_exit:
                                        raw.imported = True
                                        continue
                                
                                    att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
                                if not distinct_hour:
                                    att_value.update({'check_out': day_stop})

                            elif night_shift:
                                if distinct_hour:
                                    if night_shift.check_out:
                                        if raw.attendance_datetime < night_shift.check_in:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                        elif night_shift.check_in < raw.attendance_datetime < night_shift.check_out:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                            night_shift.check_in = raw.attendance_datetime
                                        else:
                                            att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                            night_check_in = night_shift.check_out
                                            night_shift.write({'check_in': night_check_in, 'check_out': raw.attendance_datetime})
                                    else:
                                        if night_shift.check_in < raw.attendance_datetime:
                                            night_shift.check_out = raw.attendance_datetime
                                        else:
                                            if avg < raw_float_time:
                                                night_check_out = night_shift.check_out
                                                night_shift.write({'check_in': raw.attendance_datetime, 'check_out': night_check_out})
                                            else:
                                                att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                else:
                                    if night_shift.check_in < raw.attendance_datetime:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': night_shift.check_in})
                                        night_shift.check_in = raw.attendance_datetime
                                    else:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                            else:
                                if distinct_hour:
                                    if avg < raw_float_time:
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime})
                                    else:
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                else:
                                    if raw_day_period == 'morning':
                                        att_value.update({'employee_id': employee.id, 'check_in': day_start, 'check_out': raw.attendance_datetime})
                                    else:
                                        check_in_exit = attendance_obj.search([('check_in', '<', raw.attendance_datetime),
                                                        ('check_out', '=', day_stop),#                                                     
                                                        ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                                        if check_in_exit:
                                            raw.imported = True
                                            continue
                                        att_value.update({'employee_id': employee.id, 'check_in': raw.attendance_datetime, 'check_out': day_stop})
                            if att_value:
                                att_id = attendance_obj.create(att_value)
                                raw.imported = True            
                                self._cr.commit()
                        except ValidationError as e:
                            _logger.error(e.name)
                
                else:
                
                    attendance = attendance_obj.search([('check_in', '>=', date_start),
                                                            ('check_in', '<', date_stop),
        #                                                     ('check_in','>=',str(raw_date)+ ' 00:00:00'),
        #                                                     ('check_in', '<', str(raw_date)+ ' 23:59:59'),
                                                            ('employee_id', '=', employee.id)], order='check_in desc', limit=1)
                    if attendance :
                            update_value = {}
                            try:
                                if attendance.check_out:
                                    if attendance.check_in > raw.attendance_datetime:
                                        update_value.update({'check_in': raw.attendance_datetime})
                                    elif attendance.check_out < raw.attendance_datetime :
                                        if attendance.check_out.date() == raw.attendance_datetime.date():                                    
                                            update_value.update({'check_out': raw.attendance_datetime})
                                        else:
                                            hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                            
                                    else:
                                        raw.negligible = True
                                        _logger.info(_("This raw attendance datetime %s for %s is Negligible"),
                                        format_datetime(self.env, raw.attendance_datetime, dt_format=False), raw.employee_name)
                                else:
                                    print("future_date_and_time>>")
                                    future_date_and_time = attendance.check_in + timedelta(hours = 2)
                                    print(attendance.id,">>>",attendance.check_in+ timedelta(hours=+6,minutes=+30))
                                    if attendance.check_in > raw.attendance_datetime:
                                        check_out = attendance.check_in
                                        update_value.update({'check_in': raw.attendance_datetime, 'check_out': check_out})                            
                                    elif future_date_and_time < raw.attendance_datetime:
                                        update_value.update({'check_out': raw.attendance_datetime})
                                    else:
                                        raw.imported = True
                                        self._cr.commit()
                                        continue
                                    #update_value.update({'check_out': raw.attendance_datetime})

                                updated = attendance.write(update_value)
                                if update_value:
                                    if attendance.missed:
                                        attendance.missed = False
                                        raw.imported = True            
                                        self._cr.commit()
                            except ValidationError as e:
                                attendance.missed = True
                                _logger.error(e.name)
                    else:
                        try:
                            day_start = datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
                            day_stop = datetime.strftime(date_stop, '%Y-%m-%d %H:%M:%S')
                            if calendar.time_diff_att:
                                cal_domain = [('display_type', '!=', 'line_section'), ('calendar_id', '=', calendar.id), ('dayofweek', '=', str(raw_date.weekday()))]
                                if calendar.two_weeks_calendar:
                                    week_type = int(math.floor((raw_date.toordinal() - 1) / 7) % 2)
                                    cal_domain += [('week_type', '=', str(week_type))]
                                working_hours = self.env['resource.calendar.attendance'].search(cal_domain)
                                if working_hours:
                                    if working_hours.start_end=='start':
                                        check_out =datetime.strptime(str(raw_date)+ ' 23:59:59', '%Y-%m-%d %H:%M:%S')-timedelta(hours=+6, minutes=+30)
                                        hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'check_out':check_out})
                                    else:
                                        check_in =  datetime.strptime(str(raw_date)+ ' 00:00:00', '%Y-%m-%d %H:%M:%S')-timedelta(hours=+6, minutes=+30)
                                        hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in':check_in,'check_out': raw.attendance_datetime})
                            else:
                                
                                hr_att_id = attendance_obj.create({'employee_id': employee.id, 'check_in': raw.attendance_datetime,'missed':True})
                                
                        except ValidationError as e:
                            last_attendance = attendance_obj.search([('employee_id', '=', employee.id),
                                                                    ('check_in', '=', raw.attendance_datetime)], order='id desc', limit=1)
                            
                
                            no_check_out_attendance = self.env['hr.attendance'].search([('employee_id', '=', employee.id),
                                                                                        ('check_out', '=', False),
                                                                                        ('id', '!=', last_attendance.id),
                                                                                        ], order='check_in desc', limit=1)
                            if no_check_out_attendance:
                                no_check_out_attendance.missed = True
                                raw.imported = True            
                                self._cr.commit()
                            _logger.error(e.name)
                raw.imported = True            
                self._cr.commit()
                
                
