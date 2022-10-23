from odoo import models, fields, api, _
import xlrd
import codecs
from xlrd import open_workbook
from odoo.tools.translate import _
from datetime import datetime, timedelta, timezone
import base64
import logging
from passlib.tests.backports import skip
from odoo.exceptions import ValidationError
from odoo import tools
import base64
import time
# from PIL import Image
_logger = logging.getLogger(__name__)
from odoo.modules.module import get_module_resource

header_fields = ['fingerprint id', 'date', 'in time', 'out time']

header_indexes = {}


class attendance_raw_import(models.Model):
    _name = 'attendance.raw.import'
    _description = 'Import Attendance Raw Records'

    import_file = fields.Binary(String='File', required=True)
    import_fname = fields.Char(string='Filename')
    note = fields.Text(string="Log")

    def _check_file_ext(self):
        for import_file in self.browse(self.ids):
            if '.xls' or '.xlsx' in import_file.import_fname:return True
            else:return False
        return True
    _constraints = [(_check_file_ext, "Please import Excel File!", ['import_fname'])]

    def get_excel_data(self, sheets):
        result = []
        for s in sheets:
            headers = []
            header_row = 0
            for hcol in range(0, s.ncols):
                headers.append(s.cell(header_row, hcol).value)
            result.append(headers)

            for row in range(header_row + 1, s.nrows):
                values = []
                for col in range(0, s.ncols):
                    values.append(s.cell(row, col).value)
                result.append(values)
        return result

    def get_headers(self, line):
        err_log = ''
        if line[0].strip().lower() not in header_fields:
            raise ValidationError(_ ("Error while processing the header line %s.\
            \n\nPlease check your Excel separator as well as the column header fields") % line)
        else:
            for header in header_fields:
                header_indexes[header] = -1
            col_count = 0
            for ind in range(len(line)):
                if line[ind] == '':
                    col_count = ind
                    break
                elif ind == len(line) -1:
                    col_count = ind + 1
                    break
            for i in range(col_count):
                header = line[i].strip().lower()
                if header not in header_fields:
                    err_log += '\n' + _("Invalid Excel File, Header Field '%s' is not supported!") % header
                else:
                    header_indexes[header] = i
            for header in header_fields:
                if header_indexes[header] < 0:
                    err_log += '\n' + _("Invalid Excel File, Header '%s' is Missing!") % header
                    raise ValidationError(err_log)
                    self.note = err_log

    def get_line_data(self):
        result = {}
        for header in header_fields:
            result[header] = line[header_indexes[header]]

    def import_data(self):
        attendance_raw_obj = self.env['hr.attendance.raw']
        import_file = self.import_file

        header_line = True
        lines = base64.decodestring(import_file)
        wb = open_workbook(file_contents=lines)
        excel_rows = self.get_excel_data(wb.sheets())
        value = {}
        all_data = []
        x = []
        for line in excel_rows:
            if not line or line and line[0] and line[0] in ['', '#']:
                continue
            if header_line:
                self.get_headers(line)
                header_line = False
            elif line and line[0] and line[0] not in ['#', '']:
                import_vals = {}
                for header in header_fields:
                    import_vals[header] = line[header_indexes[header]]
                all_data.append(import_vals)

        if self.note:
            import_id = self.ids[0]
            err = self.note
            self.write({'note': err, 'state': 'error'})
        else:
            for data in all_data:
                print('excel row => '+ str(all_data.index(data) + 2))
                value = {}
                # fingerprint_id = str(int(data['fingerprint id']))
                fingerprint_id = str(data['fingerprint id']).split('.')[0]
                employee_id = 0

                if fingerprint_id:
                    employee_id = self.env['hr.employee'].search([('fingerprint_id', '=', fingerprint_id)])
                in_time = data['in time']

                date = data['date']

                if in_time and type(in_time) == str:
                    excel_in_time = (datetime.strptime(in_time, "%I:%M %p") - datetime(1900,1,1)).total_seconds()
#                     excel_in_time = in_time
#                     excel_in_time = float(excel_in_time) * 86400
                    a_time = timedelta(seconds = round(excel_in_time))
                    dt_in = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
                    a_in_time = dt_in + a_time
                    # hour, minute, second = self.floatHourToTime(excel_in_time % 1)
                    # a_in_time = dt_in.replace(hour=hour, minute=minute, second=second)
                elif in_time and type(in_time) == float:
                    excel_in_time = in_time
                    excel_in_time = float(excel_in_time) * 86400
                    a_time = timedelta(seconds = round(excel_in_time))
                    dt_in = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
                    a_in_time = dt_in + a_time

                else:
                    a_in_time = None

                out_time = data['out time']
                if out_time and type(out_time) == str:
                    excel_out_time = (datetime.strptime(out_time, "%I:%M %p") - datetime(1900,1,1)).total_seconds()
#                     excel_out_time = out_time
#                     excel_out_time = float(excel_out_time) * 86400
                    a_time = timedelta(seconds = round(excel_out_time))
                    dt_out = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
                    a_out_time = dt_out + a_time
                    # hour, minute, second = self.floatHourToTime(excel_out_time % 1)
                    # a_out_time = dt_out.replace(hour=hour, minute=minute, second=second)
                elif out_time and type(out_time) == float:
                    excel_out_time = out_time
                    excel_out_time = float(excel_out_time) * 86400
                    a_time = timedelta(seconds = round(excel_out_time))
                    dt_out = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
                    a_out_time = dt_out + a_time

                else:
                    a_out_time = None
                if employee_id:
                    employee_in_values = {}
                    employee_out_values = {}
                    # if attendance_raw_obj.search([('fingerprint_id', '=', fingerprint_id),
                    #         ('attendance_datetime', '=', a_in_time)]):
                    #     raise ValidationError(_("Duplicate record found!" ))
                    if a_in_time:
                        employee_in_values = {
                            'employee_id': employee_id.id,
                            'fingerprint_id': fingerprint_id,
                            'employee_name': employee_id.name,
                            'attendance_datetime': str(a_in_time),
                            'company': employee_id.company_id.name,
                            'imported': False
                        }
                    if a_out_time:
                        employee_out_values = {
                            'employee_id': employee_id.id,
                            'fingerprint_id': fingerprint_id,
                            'employee_name': employee_id.name,
                            'attendance_datetime': str(a_out_time),
                            'company': employee_id.company_id.name,
                            'imported': False
                        }
                    if employee_in_values or employee_out_values:
                        attendance_raw_obj.create(employee_in_values)
                        attendance_raw_obj.create(employee_out_values)
                else:
                    raise ValidationError(_("The Fingerprint ID %s is not in the system!" % fingerprint_id))



