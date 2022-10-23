import io
import base64
import xlsxwriter
from odoo import models, fields, api, _
from calendar import monthrange
from datetime import datetime, date,timedelta
import calendar


MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]


class AttendanceReport(models.TransientModel):
    _name = 'attendance.report'
    _description = 'Attendance Report'

    def _get_selection(self):
        current_year = datetime.now().year
        return [(str(i), i) for i in range(current_year - 1, current_year + 10)]

    year = fields.Selection(selection='_get_selection', string='Year', required=True,
                            default=lambda x: str(datetime.now().year))
    month = fields.Selection(selection=MONTH_SELECTION, string='Month', required=True)
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    # company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    # payslip_run_id = fields.Many2one('hr.payslip.run', string='Batch')
    #job_id = fields.Many2one('hr.job', string='Position')
    resource_calendar_id = fields.Many2one('resource.calendar', string='Schedule', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    #branch_id = fields.Many2one('res.branch', string='Branch')
    excel_file = fields.Binary('Excel File')

    @api.onchange('month', 'year')
    def onchange_month_and_year(self):
        if self.year and self.month:
            if int(self.month)==1:
                self.date_from = date(year=int(self.year)-1, month=12, day=26)
                self.date_to = date(year=int(self.year), month=int(self.month),
                                day=25)
            else:
                self.date_from = date(year=int(self.year), month=int(self.month)-1, day=26)
                self.date_to = date(year=int(self.year), month=int(self.month),
                                day=25)

    def get_style(self, workbook):
        header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1})
        header_style.set_align('vcenter')
        workedday_header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1,
             'bg_color': '#ebe188'})
        workedday_header_style.set_align('vcenter')
        rule_header_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1,
             'bg_color': '#e3c1d5'})
        rule_header_style.set_align('vcenter')
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'align': 'center', 'border': 1})
        number_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0', 'align': 'vcenter', 'border': 1})
        float_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'num_format': '#,##0.00', 'align': 'vcenter', 'border': 1})
        return header_style, workedday_header_style, rule_header_style, default_style, number_style, float_style

   

    def _write_excel_data(self, workbook, sheet):
        header_style, workedday_header_style, rule_header_style, default_style, number_style, float_style = self.get_style(
            workbook)

        y_offset = 0
        if int(self.month)==1:
            x_offset = monthrange(int(self.year)-1, 12)[1]+1
        else:
            x_offset = monthrange(int(self.year), int(self.month)-1)[1]+1

        month_count = int(self.month)-1
        title_name = "Attendance Report (" + str(MONTH_SELECTION[month_count][1]) + ' - ' + str(self.year) + ')'
        sheet.merge_range(y_offset, 0,y_offset+1, 0, _("Sr"), header_style)
        sheet.merge_range(y_offset, 1,y_offset+1, 1, _("Name"), header_style)
        sheet.merge_range(y_offset,2, y_offset, x_offset, _(title_name), header_style)
        sheet.merge_range(y_offset, x_offset+1,y_offset+1, x_offset+1, _("Att"), header_style)
        sheet.merge_range(y_offset, x_offset+2,y_offset+1, x_offset+2, _("L"), header_style)
        sheet.merge_range(y_offset, x_offset+3,y_offset+1, x_offset+3, _("A"), header_style)
        sheet.merge_range(y_offset, x_offset+4,y_offset+1, x_offset+4, _("MC"), header_style)
        sheet.merge_range(y_offset, x_offset+5,y_offset+1, x_offset+5, _("D"), header_style)
        sheet.merge_range(y_offset, x_offset+6,y_offset+1, x_offset+6, _("R"), header_style)
        sheet.merge_range(y_offset, x_offset+7,y_offset+1, x_offset+7, _("Att Total"), header_style)
        sheet.merge_range(y_offset, x_offset+8,y_offset, x_offset+13, _("Leave Status"), header_style)
        sheet.write(y_offset+1,  x_offset+8, _("C"), header_style)
        sheet.write(y_offset+1,  x_offset+9, _("SC"), header_style)
        sheet.write(y_offset+1,  x_offset+10, _("Mc"), header_style)
        sheet.write(y_offset+1,  x_offset+11, _("E"), header_style)
        sheet.write(y_offset+1,  x_offset+12, _("W"), header_style)
        sheet.write(y_offset+1,  x_offset+13, _("Ttl"), header_style)
        sheet.merge_range(y_offset, x_offset+14,y_offset+1, x_offset+17, _("Remark"), header_style)
        y_offset += 1
        delta = self.date_to - self.date_from
        vals=vals_1=2
        for i in range(delta.days + 1):
            day = self.date_from + timedelta(days=i)
            sheet.write(y_offset, vals,day.strftime("%d"), header_style)
            vals +=1
        y_offset += 1
        for i in range(delta.days + 1):
            day = self.date_from + timedelta(days=i)
            sheet.write(y_offset, vals_1,day.strftime("%a"), header_style)
            vals_1 +=1
            
        

        
        # sheet.set_row(y_offset, 25)
        y_offset += 1
        col_width = [5, 25, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                     5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        for col, width in enumerate(col_width):
            sheet.set_column(col, col, width)
        employee = []
        domain = [('resource_calendar_id','=',self.resource_calendar_id.id),('department_id','=',self.department_id.id)]
        emp = self.env['hr.employee'].sudo().search(domain)
        for val in emp:
            employee.append(val.id)
        # if self.department_id:('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), 
        #     domain += [('employee_id.department_id', '=', self.department_id.id)]
        # payslips = self.env['hr.payslip'].sudo().search(domain)
        job_position = []
        
        for res in employee:
            empl = self.env['hr.employee'].sudo().search([('id','=',res)])
            if empl.job_id.id and empl.job_id.id not in job_position:
                job_position.append(empl.job_id.id)
        sr = 0
        for job in job_position:
            job_pos = self.env['hr.job'].sudo().search([('id','=',job)])
            
            
            sheet.write(y_offset,0,job_pos.name, default_style)
            y_offset +=1
            employee_1 = self.env['hr.employee'].sudo().search([('job_id','=',job)])
            for val in employee_1:
                if val.id in employee:
                    sheet.write(y_offset,0,sr+1, default_style)
                    sheet.write(y_offset,1,val.name, default_style)
                    att=2
                    a_count=r_count=l_count=att_count=0
                    for i in range(delta.days + 1):
                        day = self.date_from + timedelta(days=i)
                        self.env.cr.execute("""select is_absent from hr_attendance where check_in::date=%s and employee_id=%s and resource_calendar_id=%s and state='approve'""",(day,val.id,val.resource_calendar_id.id,))
                        result = self.env.cr.fetchall()
                        if len(result)==0:
                            sheet.write(y_offset,att,_("R"), default_style)
                            r_count +=1
                        else:
                            if result[0][0]==True:
                                sheet.write(y_offset,att,_("A"), default_style)
                                a_count +=1
                            else:
                                sheet.write(y_offset,att,1, default_style)
                                att_count+=1
                        leaves = self.env['hr.leave'].search([('request_date_from','>=',self.date_from),('request_date_from','<=',self.date_to),('employee_id','=',val.id)])
                        for leave in leaves:
                            is_leave = leave.search([('request_date_from','<=',day),('request_date_to','>=',day),('state','in',('validate1','validate'))])
                            if is_leave:
                                 sheet.write(y_offset,att,_("L"), default_style)
                                 l_count+=1
                                 r_count -=1
                        att +=1
                    sheet.write(y_offset,att,att_count, default_style)
                    sheet.write(y_offset,att+1,l_count, default_style)
                    sheet.write(y_offset,att+2,a_count, default_style)
                    sheet.write(y_offset,att+3,0, default_style)
                    sheet.write(y_offset,att+4,0, default_style)
                    sheet.write(y_offset,att+5,r_count, default_style)
                    sheet.write(y_offset,att+6,a_count+r_count+l_count+att_count, default_style)
                    c_count=sc_count=mc_count=e_count=w_count=0
                    leaves = self.env['hr.leave'].search([('request_date_from','>=',self.date_from),('request_date_from','<=',self.date_to),('employee_id','=',val.id)])
                    for leave in leaves:
                        if leave.holiday_status_id.code == "C":
                            c_count+=leave.number_of_days
                        elif leave.holiday_status_id.code == "SC":
                            sc_count+=leave.number_of_days
                        elif leave.holiday_status_id.code == "MC":
                            mc_count+=leave.number_of_days
                        elif leave.holiday_status_id.code == "E":
                            e_count+=leave.number_of_days
                        elif leave.holiday_status_id.code == "W":
                            w_count+=leave.number_of_days
                    sheet.write(y_offset,att+7,c_count, default_style)
                    sheet.write(y_offset,att+8,sc_count, default_style)
                    sheet.write(y_offset,att+9,mc_count, default_style)
                    sheet.write(y_offset,att+10,e_count, default_style)
                    sheet.write(y_offset,att+11,w_count, default_style)
                    sheet.write(y_offset,att+12,c_count+sc_count+mc_count+e_count+w_count, default_style)
                    y_offset +=1
                    
            
        
        

       
       

    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        month_name = dict(self._fields['month'].selection).get(self.month) + ' - ' + self.year
        report_name = 'Attendance Report for ' + month_name + '.xlsx'
        sheet = workbook.add_worksheet(month_name)
        self._write_excel_data(workbook, sheet)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        excel_file = base64.encodestring(generated_file)
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=attendance.report&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, report_name),
                'target': 'new',
            }