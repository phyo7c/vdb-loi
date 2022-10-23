from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import xlrd
import base64
from xlrd import open_workbook
from calendar import monthrange
import pytz

header_fields = ['sr', 'duty time', 'remark']
ignore_fields = ['rest day']


class PlanningImport(models.Model):
    _name = 'planning.import'
    _description = 'Import Planning Records'

    file = fields.Binary('File')
    pl_fname = fields.Char('Filename', size=128, required=True, default='')

    @api.model
    def _check_file_ext(self):
        for import_file in self.browse(self.id):
            if '.xls' in import_file.pl_fname:
                return True
            else:
                return False
        return True

    _constraints = [(_check_file_ext, "Please import Excel file!", ['pl_fname'])]

    @staticmethod
    def check_date(duty_date):
        if len(duty_date) != 1:
            raise UserError("Only one date require!")
        try:
            float(duty_date[0])
            date_data = duty_date[0]
        except ValueError:
            raise UserError("Date Format is Wrong!")
        except IndexError:
            raise UserError("Date is Missing!")
        return date_data

    @staticmethod
    def check_headers_get_dates(headers, total_day, full_date):
        duty_dates = []
        for header in headers:
            if isinstance(header, str):
                if header.lower() not in header_fields:
                    raise UserError(_('%s fields is Missing!', header))
            elif (header - int(header)) != 0:
                raise UserError(_('Giving Date (%s) should not be Decimal Number!', header))
            else:
                if header > total_day:
                    raise UserError(_('Giving Date (%s) is Wrong!', int(header)))
                else:
                    duty_dates.append(datetime.date(full_date.year, full_date.month, int(header)))
        return duty_dates

    @staticmethod
    def check_duty_list(headers, duty_lists):
        lists_of_duty = {}
        if duty_lists:
            for duty_list in duty_lists:
                if len(headers[2:]) != len(duty_list[2:]):
                    raise UserError("Duty Groups and Dates are different!")
                else:
                    lists_of_duty[duty_list[1]] = duty_list[2:-1]
        else:
            raise UserError("Duty Group List is missing")
        return lists_of_duty

    @staticmethod
    def check_time_format(self, lists_of_duty, duty_dates):
        duty_dicts = {}
        duty_date_group_dicts = {}
        for duty_time, group_lists in lists_of_duty.items():
            time_lists = []
            index = 0
            if duty_time.lower() not in ignore_fields:
                start_end_time = self.check_time_length(duty_time, '-', duty_dates)
                for time in start_end_time:
                    time_lists.append(self.check_time_length(time, ':', duty_dates))
                duty_dicts = dict(zip(time_lists[0], time_lists[1]))
                for key, value in duty_dicts.items():
                    if group_lists[index]:
                        if group_lists[index] in duty_date_group_dicts.keys():
                            duty_date_group_dicts[group_lists[index]].update({key: value})
                        else:
                            duty_date_group_dicts[group_lists[index]] = {key: value}
                    index += 1
        return duty_date_group_dicts

    @staticmethod
    def check_time_length(duty_time, spliter, duty_dates):
        try:
            start_end_time = duty_time.replace(" ", "").split(spliter)
        except AttributeError:
            raise UserError("Time format must be '00:00 - 00:00'.")
        if len(start_end_time) != 2:
            raise UserError("Time format must be '00:00 - 00:00'.")
        if spliter == ':':
            start_end_date_time = []
            try:
                changed_time = datetime.time(int(start_end_time[0]), int(start_end_time[1]))
                for duty_date in duty_dates:
                    start_end_date_time.append(datetime.datetime.combine(duty_date, changed_time))
            except ValueError as msg:
                raise UserError(_("Invalid Time Format : (%s)", msg))
            return start_end_date_time
        else:
            return start_end_time

    @staticmethod
    def import_to_planning(self, duty_date_group_dicts):
        record_list = []
        local_format = '%Y-%m-%d %H:%M:%S'
        for groups, start_end_time in duty_date_group_dicts.items():
            for start_time, end_time in start_end_time.items():
                search_group_id = self.env['hr.employee.groups'].search([('name', '=', groups)])
                if not search_group_id:
                    raise UserError(_("The (%s) group is not exist!", groups))
                search_emp_ids = self.env['hr.employee'].search([('group_id', '=', search_group_id.id)])
                start_time += datetime.timedelta(hours=-7, minutes=30)
                end_time += datetime.timedelta(hours=-7, minutes=30)
                if end_time < start_time:
                    end_time += datetime.timedelta(days=1)
                for search_emp_id in search_emp_ids:
                    check_exist = self.env['planning.slot'].search([('employee_id', '=', search_emp_id.id),
                                                                    ('start_datetime', '=', start_time),
                                                                    ('end_datetime', '=', end_time)])
                    if not check_exist:
                        record_list.append({
                            'resource_id': search_emp_id.resource_id.id,
                            'employee_id': search_emp_id.id,
                            'start_datetime': start_time,
                            'end_datetime': end_time,
                            'check_date': start_time.date(),
                        })
        if len(record_list) < 1:
            raise UserError(_('No Updated List!'))
        self.env['planning.slot'].create(record_list)

    def import_data(self):
        import_file = self.browse(self.id).file
        lines = base64.decodebytes(import_file)
        wb = open_workbook(file_contents=lines)
        duty_groups = []
        for s in wb.sheets():
            for row in range(0, s.nrows):
                duty_group = []
                for col in range(0, s.ncols):
                    duty_group.append(s.cell(row, col).value)
                duty_groups.append(duty_group)
            duty_date = list(filter(None, duty_groups[1]))
            date_data = self.check_date(duty_date)

            full_date = xlrd.xldate.xldate_as_datetime(date_data, 0).date()

            total_day = monthrange(full_date.year, full_date.month)[1]
            headers = list(filter(None, duty_groups[2]))
            duty_dates = self.check_headers_get_dates(headers, total_day, full_date)

            duty_lists = duty_groups[4:]
            lists_of_duty = self.check_duty_list(headers, duty_lists)

            duty_date_group_dicts = self.check_time_format(self, lists_of_duty, duty_dates)

            self.import_to_planning(self, duty_date_group_dicts)
