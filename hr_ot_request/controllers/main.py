# -*- coding: utf-8 -*-

import re
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import datetime, date, time, timedelta
import calendar
import datetime
from calendar import monthrange
import math
    
def float_to_time(value):
    if value < 0:
        value = abs(value)

    hour = int(value)
    minute = round((value % 1) * 60)

    if minute == 60:
        minute = 0
        hour = hour + 1
    return time(hour, minute)


def time_to_float(value):
    return value.hour + value.minute / 60 + value.second / 3600

class SaleExcelReportController(http.Controller):
    @http.route([
        '/overtime_request/excel_report/<model("overtime.request.report"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_sale_excel_report(self,wizard=None,**args):
        # the wizard parameter is the primary key that odoo sent 
        # with the get_excel_report method in the ng.sale.wizard model
        # contains salesperson, start date, and end date

        # create a response with a header in the form of an excel file
        # so the browser will immediately download it
        # The Content-Disposition header is the file name fill as needed
        
        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('Overtime Request Report' + '.xlsx'))
                    ]
                )

        # create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # create some style to set up the font type, the font size, the border, and the aligment
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'center'})
        text_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'left'})
        number_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'right'})

        # loop all selected user/salesperson
        # for user in wizard.user_id:
        
            # create worksheet/tab per salesperson 
        sheet = workbook.add_worksheet('Overtime Request Report')
        # set the orientation to landscape
        sheet.set_landscape()
        # set up the paper size, 9 means A4
        sheet.set_paper(9)
        # set up the margin in inch
        sheet.set_margins(0.5,0.5,0.5,0.5)

        # set up the column width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:I', 22)

        # the report title
        # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
        sheet.merge_range('A1:I1', 'Overtime Report Request', title_style)
        
        # table title
        sheet.write(1, 0, 'No.', header_style)
        sheet.write(1, 1, 'Employee', header_style)
        sheet.write(1, 2, 'Branch', header_style)
        sheet.write(1, 3, 'Department', header_style)
        sheet.write(1, 4, 'Position', header_style)
        sheet.write(1, 5, 'Overtime From Datetime', header_style)
        sheet.write(1, 6, 'Overtime To Datetime', header_style)
        sheet.write(1, 7, 'Overtime Duration', header_style)
        sheet.write(1, 8, 'Overtime Amount', header_style)
        sheet.write(1, 9, 'Reasons', header_style)

        row = 2
        number = 1

        # search the sales order  
        request_ids = request.env['ot.request'].search([('start_date', '>=', wizard.date_from), ('end_date', '<=', wizard.date_to),('state','=','verify')])
        ot_duration = 0
        for req in request_ids:
            for line in req.request_line:
               
                if line.employee_id.contract_id:
                    if line.employee_id.contract_id.wage > 300000:
                        attendance = request.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id),'|',
                                                        ('check_in', '>=', req.start_date),('check_in', '<=', req.start_date),'|',
                                                        ('check_out', '<=', req.start_date),('check_out', '>=', req.start_date),
                                                        ('state', '=', 'approve'),('ot_hour','>',0)])
                        if attendance:
                            # if attendance.ot_hour < req.duration:
                            #     ot_duration =   attendance.ot_hour
                            # else:      
                            #     ot_duration =  req.duration  
                        # else:      
                        #     ot_duration =  req.duration                 
                            sheet.write(row, 0, number, text_style)
                            sheet.write(row, 1, line.employee_id.name, text_style)
                            sheet.write(row, 2, line.employee_id.branch_id and line.employee_id.branch_id.name or '', text_style)
                            sheet.write(row, 3, line.employee_id.department_id and line.employee_id.department_id.name or '', text_style)
                            sheet.write(row, 4, line.employee_id.job_id and line.employee_id.job_id.name or '', text_style)
                            sheet.write(row, 5, req.start_date and req.start_date.strftime('%d-%m-%Y %H:%M:%S UTC'), text_style)
                            sheet.write(row, 6, req.end_date and req.end_date.strftime('%d-%m-%Y %H:%M:%S UTC'), text_style)
                            sheet.write(row, 7, ot_duration, text_style)
                            sheet.write(row, 8, (line.employee_id.contract_id.wage/monthrange(req.end_date.year, req.end_date.month)[1])*line.employee_id.contract_id.ot_rate, text_style)
                            sheet.write(row, 9, req.reason, text_style)
                        
                
                    elif line.employee_id.contract_id.wage < 300000:
                        if line.employee_id.resource_calendar_id.two_weeks_calendar:
                            week_type = int(math.floor((req.start_date.toordinal() - 1) / 7) % 2)

                            working_time = request.env['resource.calendar.attendance'].search([('dayofweek','=',req.start_date.weekday()),('calendar_id','=',line.employee_id.resource_calendar_id.id),('week_type', '=', str(week_type))])
                        else:
                            working_time = request.env['resource.calendar.attendance'].search([('dayofweek','=',req.start_date.weekday()),('calendar_id','=',line.employee_id.resource_calendar_id.id)])

                        if working_time:
                            ot_allow = time_to_float(float_to_time(working_time.hour_to))+1.08
                            ot_request = round(int((req.end_date+timedelta(hours=6,minutes=30)).strftime('%H'))+int((req.end_date+timedelta(hours=6,minutes=30)).strftime('%M'))/60,2)
                            attendance = request.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id),'|',
                                                        ('check_in', '>=', req.start_date),('check_in', '<=', req.start_date),'|',
                                                        ('check_out', '<=', req.start_date),('check_out', '>=', req.start_date),
                                                        ('state', '=', 'approve'),('ot_hour','>',0)])
                            if attendance:
                                if attendance.ot_hour < req.duration:
                                    ot_duration =   attendance.ot_hour
                                else:      
                                    ot_duration =  req.duration  
                                start_date = req.start_date-timedelta(hours=6,minutes=30)
                                end_date = req.end_date-timedelta(hours=6,minutes=30)
                                if ot_request>ot_allow:
                                    sheet.write(row, 0, number, text_style)
                                    sheet.write(row, 1, line.employee_id.name, text_style)
                                    sheet.write(row, 2, line.employee_id.branch_id and line.employee_id.branch_id.name or '', text_style)
                                    sheet.write(row, 3, line.employee_id.department_id and line.employee_id.department_id.name or '', text_style)
                                    sheet.write(row, 4, line.employee_id.job_id and line.employee_id.job_id.name or '', text_style)
                                    sheet.write(row, 5, req.start_date and start_date.strftime('%d-%m-%Y %H:%M:%S'), text_style)
                                    sheet.write(row, 6, req.end_date and end_date.strftime('%d-%m-%Y %H:%M:%S'), text_style)
                                    sheet.write(row, 7, ot_duration, text_style)
                                    sheet.write(row, 8, ((line.employee_id.contract_id.wage/monthrange(req.end_date.year, req.end_date.month)[1])/line.employee_id.resource_calendar_id.hours_per_day)*ot_duration, text_style)
                                    sheet.write(row, 9, req.reason, text_style)
                                
                    
        #attendance_ids = request.env['hr.attendance'].search([('ot_hour', '>=', 1.0), ('check_out', '<=', wizard.date_to)])
        # attendance_ids = request.env['hr.attendance'].search([])

        # # attendance_raw_ids = request.env['hr.attendance.raw']
        # working_time_id = request.env['resource.calendar'].search([('name','>=', 'Standard 40 hours/week')])
        # for w_time in working_time_id.attendance_ids:
            
        #     for ot in attendance_ids:
        #         # the report content
        #         sheet.write(row, 0, number, text_style)
        #         sheet.write(row, 1, ot.employee_id.name, text_style)
        #         sheet.write(row, 2, str(ot.check_in), text_style)
        #         sheet.write(row, 3, ot.employee_id.name, text_style)
        #         sheet.write(row, 4, ot.employee_id.name, text_style)
        #         sheet.write(row, 5, ot.employee_id.name, text_style)
        #         sheet.write(row, 6, str(ot.check_in), text_style)
        #         sheet.write(row, 7, ot.employee_id.name, text_style)
        #         sheet.write(row, 8, ot.employee_id.name, text_style)

        #         row += 1
        #         number += 1

                # create a formula to sum the total sales
                # sheet.merge_range('A' + str(row+1) + ':D' + str(row+1), 'Total', text_style)
                # sheet.write_formula(row, 4, '=SUM(E3:E' + str(row) + ')', number_style)

        # return the excel file as a response, so the browser can download it
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response