from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class DeductionConfig(models.Model):    
    _name = 'deduction.config'
    # _rec_name = 'combination'
    _description = 'Deduction Configuration'    

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    # combination = fields.Char(string='Combination', compute='_compute_fields_combination')
    
    # @api.depends('name', 'code')
    # def _compute_fields_combination(self):
    #     for test in self:
    #         test.combination = '[' + test.code + ']' + test.name

    def name_get(self):
        result = []
        for record in self:
            if record.name and record.code:
                result.append((record.id, "[{}] {}".format(record.code, record.name)))
        return result



class Deduction(models.Model):
    _name = 'hr.deduction'
    _description = 'Deduction'   
    _rec_name = 'deduction_config_id'

    deduction_config_id = fields.Many2one('deduction.config', string='Deduction Name')
    amount = fields.Float(string='Amount')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    effective_date = fields.Date(string='Effective Date', copy=False)
    effective_type = fields.Selection([('one_time', 'One-time'),
                                       ('monthly', 'Monthly'),
                                       ('yearly', 'Yearly')], string="Effective Type", default='one_time')
    end_date = fields.Date(string='End Date')
    code = fields.Char(string='Code', related='deduction_config_id.code',store=True)
    
        
    
    def init(self):
        self._cr.execute("select 1 from information_schema.constraint_column_usage where table_name = 'hr_deduction' and constraint_name = 'hr_deduction_code_uniq'")
        if self._cr.rowcount:
            self._cr.execute("ALTER TABLE hr_deduction DROP CONSTRAINT hr_deduction_code_uniq")

    @api.constrains('deduction_config_id', 'employee_id', 'effective_date')
    def check_duplicate_record(self):
        for ded in self:
            if ded.deduction_config_id and ded.employee_id and ded.effective_date:
                domain = [('employee_id', '=', self.employee_id.id),
                          ('deduction_config_id', '=', self.deduction_config_id.id),
                          ('effective_type', '=', self.effective_type),
                          ('id', '!=', self.id)]
                if self.search(domain).filtered(lambda r: r.effective_date.month == ded.effective_date.month and r.effective_date.year == ded.effective_date.year):
                    raise ValidationError(_('Duplicate Record!!!'))
