import json
import io
from typing import Sequence
import xlsxwriter
from odoo import models, api, fields, _
from odoo.tools import date_utils
from dateutil import parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class JobPositionChecklistReport(models.AbstractModel):
    _name = 'report.employee_performance.report_job_position_checklist_qweb'
    _description = 'Job Position Checklist Report'

    def get_pms_list(self, fiscal_year, company_id, branch_id, job_ids):
        # pms_obj = self.env['employee.performance'].sudo().search([('company_id', '=', company_id.id),
        #                                                         ('branch_id', '=', branch_id.id),
        #                                                         ('job_id', 'in', job_ids.ids),
        #                                                         ('date_range_id', '=', fiscal_year.id)])
        job_position_obj = self.env['hr.employee'].sudo().search([('company_id', '=', company_id.id),
                                                                ('branch_id', '=', branch_id.id),
                                                                ('job_id', 'in', job_ids.ids)])
        vals = {}
        if job_position_obj:
            for rec in job_position_obj:
                if rec.job_id.id in vals:
                    temp_list = vals.get(rec.job_id.id)
                    count = temp_list[6] + 1
                    temp_list[6] = count
                    vals.update({rec.job_id.id: temp_list})
                else:
                    val_list = []
                    current_position_count = 1
                    pms_count = len(self.env['employee.performance'].sudo().search([('company_id', '=', rec.company_id.id), ('branch_id', '=', rec.branch_id.id), ('job_id', '=', rec.job_id.id)]))
                    val_list.append(fiscal_year.name)
                    val_list.append(rec.job_id.name)
                    val_list.append(rec.company_id.name)
                    val_list.append(rec.branch_id.name)
                    val_list.append(rec.job_id.name)
                    val_list.append(pms_count)
                    val_list.append(current_position_count)
                    vals.update({rec.job_id.id: val_list})
        # if pms_obj:
        #     for pms in pms_obj:
        #         if pms.job_id.id in vals:
        #             temp_list = vals.get(pms.job_id.id)
        #             count = temp_list[5] + 1
        #             temp_list[5] = count
        #             vals.update({pms.job_id.id: temp_list})
        #         else:
        #             val_list = []
        #             pms_count = 1
        #             current_position_count = len(self.env['hr.employee'].sudo().search([('company_id', '=', pms.company_id.id), ('branch_id', '=', pms.branch_id.id), ('job_id', '=', pms.job_id.id)]))
        #             val_list.append(pms.date_range_id.name)
        #             val_list.append(pms.job_id.name)
        #             val_list.append(pms.company_id.name)
        #             val_list.append(pms.branch_id.name)
        #             val_list.append(pms.name)
        #             val_list.append(pms_count)
        #             val_list.append(current_position_count)
        #             vals.update({pms.job_id.id: val_list})
        return vals

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('ids', data.get('active_ids'))

        fiscal_year = self.env.context.get('fiscal_year')
        company_id = self.env.context.get('company_id')
        branch_id = self.env.context.get('branch_id')
        job_ids = self.env.context.get('job_ids')

        if not fiscal_year:
            fiscal_year = self.env['job.position.checklist.wizard'].browse(
                docids).fiscal_year
        if not company_id:
            company_id = self.env['job.position.checklist.wizard'].browse(
                docids).company_id
        if not branch_id:
            branch_id = self.env['job.position.checklist.wizard'].browse(
                docids).branch_id
        if not job_ids:
            job_ids = self.env['job.position.checklist.wizard'].browse(
                docids).job_ids
    
        pms = self.env['employee.performance'].sudo().search([('company_id', '=', company_id.id),
                                                            ('branch_id', '=', branch_id.id),
                                                            ('job_id', 'in', job_ids.ids),
                                                            ('date_range_id', '=', fiscal_year.id)])

        get_pms_list = self.get_pms_list(fiscal_year, company_id, branch_id, job_ids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'employee.performance',
            'fiscal_year': fiscal_year,
            'company_id': company_id,
            'branch_id': branch_id,
            'job_id': job_ids,
            'docs': pms,
            'get_pms_list': get_pms_list,
        }


class ReportJobPositionChecklist(models.AbstractModel):
    _name = 'report.employee_performance.report_job_position_checklist'
    _inherit = 'account.report'
    _description = 'Job Position Checklist Report'

    def get_report_filename(self, options):
        return 'Job Position Checklist Report'
    
    def get_xlsx(self, options, response=None):
        filter = options.get('form') or {}
        job_position_obj = self.env['hr.employee'].sudo().search([('company_id', '=', filter['company_id']),
                                                                ('branch_id', '=', filter['branch_id']),
                                                                ('job_id', 'in', filter['job_ids'])])
        date_range_id = filter['fiscal_year']
        date_range = self.env['performance.date.range'].sudo().browse(date_range_id)
        
        vals = {}
        if job_position_obj:
            for rec in job_position_obj:
                if rec.job_id.id in vals:
                    temp_list = vals.get(rec.job_id.id)
                    count = temp_list[6] + 1
                    temp_list[6] = count
                    vals.update({rec.job_id.id: temp_list})
                else:
                    val_list = []
                    current_position_count = 1
                    pms_count = len(self.env['employee.performance'].sudo().search([('company_id', '=', rec.company_id.id), ('branch_id', '=', rec.branch_id.id), ('job_id', '=', rec.job_id.id)]))
                    val_list.append(date_range.name)
                    val_list.append(rec.job_id.name)
                    val_list.append(rec.company_id.name)
                    val_list.append(rec.branch_id.name)
                    val_list.append(rec.job_id.name)
                    val_list.append(pms_count)
                    val_list.append(current_position_count)
                    vals.update({rec.job_id.id: val_list})
        print("vals : ", vals)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Job Position Checklist Report')
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        default_number_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': '#,###'})
        title_style = workbook.add_format({'font_name': 'Arial', 'font_size': 15, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'bold': True, 'bg_color': '#EEEEEE', 'align': 'center'})

        col_width = [10, 25, 30, 30, 30, 20, 25, 25]
        for col, width in enumerate(col_width):
            worksheet.set_column(col, col, width)
        
        worksheet.write(0, 3, "Job Position Checklist Report", title_style)
        worksheet.write(2, 0, "No.", header_style)
        worksheet.write(2, 1, "Fiscal Year", header_style)
        worksheet.write(2, 2, "Job Position", header_style)
        worksheet.write(2, 3, "Company", header_style)
        worksheet.write(2, 4, "Branch", header_style)
        worksheet.write(2, 5, "Key Performance Template", header_style)
        worksheet.write(2, 6, "Created Job Position in PMS", header_style)
        worksheet.write(2, 7, "Current Job Position", header_style)

        row = 3
        sequence = 0
        for x in vals.values():
            sequence += 1
            worksheet.write(row, 0, sequence or '', default_style)
            worksheet.write(row, 1, x[0] or '', default_style)
            worksheet.write(row, 2, x[1] or '', default_style)
            worksheet.write(row, 3, x[2] or '', default_style)
            worksheet.write(row, 4, x[3] or '', default_style)
            worksheet.write(row, 5, x[4] or '', default_style)
            worksheet.write(row, 6, x[5] or '', default_number_style)
            worksheet.write(row, 7, x[6] or '', default_number_style)
            row += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def xlsx_export(self, datas):
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': 'report.employee_performance.report_job_position_checklist',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'financial_id': self.env.context.get('id'),
                     }
        }