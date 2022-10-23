from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class OTAllowance(models.Model):    
    _name = 'ot.allowance'
    _description = 'OT Allowance'    
    
    job_grade_id = fields.Many2one('job.grade',string='Job Grade')
    amount = fields.Float(string='Amount')
    line_ids = fields.One2many('ot.allowance.line', 'ot_allowance_id', string='Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    
    @api.onchange('job_grade_id')
    def onchange_job_grade_id(self):
        
        new_lines = self.env['ot.allowance.line']
        if self.job_grade_id:
            domain = [('job_grade_id', '=', self.job_grade_id.id),('state', '=', 'open')]
            contracts = self.env['hr.contract'].search(domain)
            if contracts:                
                for contract in contracts:
                    new_line_value = {
                                        'employee_id': contract.employee_id.id
                                    }
                    new_line = new_lines.new(new_line_value)
                    new_lines += new_line
                self.line_ids = new_lines
        
    def approve(self):
        
        for line in self.line_ids:
            contract = self.env['hr.contract'].search([('employee_id', '=', line.employee_id.id),('state', '=', 'open')])
            if contract:
                contract.write({
                                "ot_allowance_per_day": line.ot_allowance_id.amount
                            })
        self.state = 'approve'
        
    def reset_to_draft(self):

        self.state = 'draft'
        
class OTAllowanceLine(models.Model):
    _name = 'ot.allowance.line'
    _description = 'OT Allowance Line'
    
    ot_allowance_id = fields.Many2one('ot.allowance', string='OT Allowance', ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    