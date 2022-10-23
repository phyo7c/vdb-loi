from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import sys
import tempfile
import binascii
import xlrd
import base64
import io
import csv
from xlrd import open_workbook
from itertools import product
from pytz import timezone, UTC
# from odoo.addons.hr_travel_request.models.hr_travel_request import get_utc_datetime, get_local_datetime, float_to_time
from dateutil.relativedelta import relativedelta

header_fields = ['name', 'department_ids', 'start_date', 'end_date', 'duration', 'reason','requested_employee_id', 'employee_id', 'email','state','remark_line','mail_sent']

class ImportOvertimeRequest(models.TransientModel):
    _name='import.ot.request'
    _description='Import Overtime Request'

    file = fields.Binary('File')
    sl_fname = fields.Char('Filename', size=128, required=True, default='')
    
    @api.model     
    def _check_file_ext(self):
        for import_file in self.browse(self.id):
            if '.xls' in import_file.sl_fname:return True
            else: return False
        return True
     
    _constraints = [(_check_file_ext, "Please import Excel file!", ['sl_fname'])]
    
    def find_emp(self,requested_employee_id):
        if not requested_employee_id:
            return False
        emp_id = self.env['hr.employee'].search([('name','=',requested_employee_id)])
        if emp_id:
            return emp_id.id
        else:
            raise UserError(_('%s does not exist in system' % requested_employee_id))
        
    def find_employee(self,employee_id):
        if not employee_id:
            return False
        employee_id = self.env['hr.employee'].sudo().search([('name','=',employee_id)])
        if employee_id:
            return employee_id.id
        else:
            raise UserError(_('%s does not exist in system' % employee_id))
        
    def create_ot_request_line(self,request_id,values):
        ot_request_line_id = self.env['ot.request.line'].create({
                'employee_id':self.find_employee(values.get('employee_id')),
                'start_date':values.get('start_date'),
                'end_date':values.get('end_date'),
                'email':values.get('email'),
                'state':values.get('state'),
                'remark_line':values.get('remark_line'),
                'mail_sent':values.get('mail_sent'),
                'request_id':request_id.id
                })

    def create_ot_request(self, value, branch_id):
        ot_list_id = []
        ot_request_id = self.env['ot.request']
        if ot_request_id:
            if ot_request_id.requested_employee_id.name == value.get('name'):
                self.create_ot_request_line(ot_request_id,value)
        else:
            request_id = self.env['ot.request'].create({
                'name':value.get('name'),
                'start_date':value.get('start_date'),
                'end_date':value.get('end_date'),
                'duration':value.get('duration'),
                'reason':value.get('reason'),
                'requested_employee_id':self.find_emp(value.get('requested_employee_id')),
                })
            self.create_ot_request_line(request_id,value)
            ot_list_id.append(request_id.id)
        if value.get('department_ids'):
            ids = value.get('department_ids').split(',')
            for name in ids:                
                dept= self.env['hr.department'].search([('name', '=', name),('branch_id', '=', branch_id)])                
                if not dept:
                    raise Warning(_('"%s" Department not in your system') % name)     
                else:
                    self.env.cr.execute('insert into hr_department_ot_request_rel(ot_request_id,hr_department_id) values(%s,%s);', (request_id.id,dept.id,))          
        
    def import_ot_request(self):
        data = self.browse(self.id)
        import_file = data.file
        
        err_log = ''
        header_line = False
                
        lines = base64.decodestring(import_file)
        wb = open_workbook(file_contents=lines)
        excel_rows = []
        for s in wb.sheets():
            # header
            headers = []
            header_row = 0
            for hcol in range(0, s.ncols):
                headers.append(s.cell(header_row, hcol).value)
            # add header
            excel_rows.append(headers)
            for row in range(header_row + 1, s.nrows):
                values = []
                for col in range(0, s.ncols):
                    values.append(s.cell(row, col).value)
                excel_rows.append(values)

        count = head_count = 0
        prev_row_count = 1
        for ln in excel_rows:
            if not ln :
                continue
            if not header_line:
                for l in header_fields:
                    if str(l).strip().lower() in [str(x).strip().lower() for x in ln]:
                        head_count = head_count + 1
                if head_count < 1:                    
                    raise UserError(_('Illegal Header Fields!'))    
                else:
                    if ln:
                        for l in header_fields:
                            if str(l).strip() in [str(x).strip().lower() for x in ln]:
                                y=0
                            else:
                                # check the columns without contained the header fields
                                ln.append(str(l))
                                count = count + 1
                                val = count     
                    header_line = True
                    column_cnt = 0
                    sheet = wb.sheet_by_index(0)
                    values = {}
                    for cnt in range(len(ln)):
                        if ln[cnt] == '':
                            column_cnt = cnt
                            break
                        elif cnt == len(ln) - 1:
                            column_cnt = cnt + 1
                            break
                    for i in range(column_cnt):
                        # header fields
                        header_field = ln[i].strip().lower()
                        if header_field not in header_fields:
                            err_log += '\n' + _("Invalid CSV File, Header Field '%s' is not supported !") % ln[i] 
                    for row_no in range(sheet.nrows):
                        val = {}
                        existing_ot = None
                        if row_no <= 0:
                            fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                        else:
                            line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                            if line[1] and line[2] and line[3]:
                                date_tuple = xlrd.xldate_as_tuple(float(line[2]), wb.datemode)
                                start_date = datetime(*date_tuple).strftime('%Y-%m-%d %H:%M:%S')
                                date_tuples = xlrd.xldate_as_tuple(float(line[3]), wb.datemode)
                                end_date = datetime(*date_tuples).strftime('%Y-%m-%d %H:%M:%S')   
                                self.env.cr.execute("""select (%s::TIMESTAMP) - interval '6 hour 30mins'""",(start_date,))
                                start_date = self.env.cr.fetchone()[0]      
                                self.env.cr.execute("""select (%s::TIMESTAMP) - interval '6 hour 30mins'""",(end_date,))
                                end_date = self.env.cr.fetchone()[0]   
                            if not line[1]:
                                prev_row = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no-prev_row_count)))
                                if prev_row and prev_row[2] and prev_row[3]:
                                    date_tuple = xlrd.xldate_as_tuple(float(prev_row[2]), wb.datemode)
                                    prev_start_date = datetime(*date_tuple).strftime('%Y-%m-%d %H:%M:%S')
                                    date_tuples = xlrd.xldate_as_tuple(float(prev_row[3]), wb.datemode)
                                    prev_end_date = datetime(*date_tuples).strftime('%Y-%m-%d %H:%M:%S')   
                                    self.env.cr.execute("""select (%s::TIMESTAMP) - interval '6 hour 30mins'""",(prev_start_date,))
                                    prev_start_date = self.env.cr.fetchone()[0]      
                                    self.env.cr.execute("""select (%s::TIMESTAMP) - interval '6 hour 30mins'""",(prev_end_date,))
                                    prev_end_date = self.env.cr.fetchone()[0] 
                                    existing_ot = self.env['ot.request'].search([('name', '=', prev_row[0]),('start_date', '=', prev_start_date),('end_date', '=', prev_end_date),('duration', '=', prev_row[4])])
                            emp= self.env['hr.employee'].search([('name', '=', line[7])])
                            if existing_ot:
                                prev_row_count = prev_row_count + 1
                                line_id = self.env['ot.request.line'].create({
                                                                        'start_date': start_date,
                                                                        'end_date': end_date,
                                                                        'employee_id': emp.id,
                                                                        'email': line[8],
                                                                        'state': line[9],
                                                                        'remark_line': line[10],
                                                                        'mail_sent': line[11],
                                                                        'request_id':existing_ot.id
                                                                         })        
                            else:
                                prev_row_count = 1
                                values.update( {
                                                    'name':line[0],
                                                    'department_ids': line[1],
                                                    'start_date': start_date,
                                                    'end_date': end_date,
                                                    'duration': line[4],
                                                    'reason': line[5],
                                                    'requested_employee_id':line[6],
                                                    'employee_id': line[7],
                                                    'email': line[8],
                                                    'state': line[9],
                                                    'remark_line': line[10],
                                                    'mail_sent': line[11],
                                                    })
                                res = self.create_ot_request(values,emp.branch_id.id)
                                