from odoo import api, fields, models, _
from datetime import date, datetime, timedelta


class JobPositionChecklistWizard(models.TransientModel):
    _name = 'job.position.checklist.wizard'
    _description = 'Job Position Checklist Wizard'

    fiscal_year = fields.Many2one('performance.date.range', string='Fiscal Year')
    company_id = fields.Many2one('res.company', string='Company')
    branch_id = fields.Many2one('res.branch', string='Branch')
    job_ids = fields.Many2many('hr.job', string='Position')

    def get_report_pdf(self):
        data = {
            'ids':
            self.ids,
            'model':
            'employee.performance',
            'form':
            self.read([
                'fiscal_year', 'company_id', 'branch_id', 'job_ids'
            ])[0]
        }
        return self.env.ref('employee_performance.job_position_checklist_report').report_action(self, data=data)

    def print_xlsx(self):
        data_obj = self.env['report.employee_performance.report_job_position_checklist']
        datas = {
            'form':
                {
                    'fiscal_year': self.fiscal_year.id,
                    'company_id': self.company_id.id,
                    'branch_id': self.branch_id.id,
                    'job_ids': self.job_ids.ids,
                }
        }
        return data_obj.xlsx_export(datas)        