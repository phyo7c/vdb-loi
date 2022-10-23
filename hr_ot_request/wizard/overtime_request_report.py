# -*- coding: utf-8 -*-


from odoo import api, fields, models,_
from datetime import datetime
from odoo.exceptions import ValidationError

### wizard
class OtRequestReport(models.TransientModel):
    _name = "overtime.request.report"

    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    branch = fields.Many2one('res.branch', string='Branch')
    department_ids = fields.Many2many('hr.department', string='Departments')
    user_id = fields.Many2one(
        'res.users', string='Salesperson', default=lambda self: self.env.user)

    @api.onchange('date_to')
    def onchange_date_to(self):
        for record in self:
            if record.date_to and record.date_to < record.date_from:
                raise ValidationError("From Date must be less than To date")
            else:
                pass

    
                
    def ot_request_report_wizard(self):
        if self.date_from and self.date_to and self.branch and self.department_ids:        

            return {
                'type': 'ir.actions.act_url',
                'url': '/overtime_request/excel_report/%s' % (self.id),
                'target': 'new',
            }

        