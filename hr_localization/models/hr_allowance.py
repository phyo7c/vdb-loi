from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class AllowanceConfig(models.Model):    
    _name = 'allowance.config'
    # _rec_name = 'combination'
    _description = 'Allowance Configuration'    

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


class Allowance(models.Model):    
    _name = 'hr.allowance'
    _description = 'Allowance'   
    _rec_name = 'allowance_config_id' 

    allowance_config_id = fields.Many2one('allowance.config', string='Name')
    amount = fields.Float(string='Amount')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    effective_date = fields.Date(string='Effective Date', copy=False)
    effective_type = fields.Selection([('one_time', 'One-time'),
                                       ('monthly', 'Monthly'),
                                       ('yearly', 'Yearly')], string="Effective Type", default='one_time')
    end_date = fields.Date(string='End Date')
    code = fields.Char(string='Code', related='allowance_config_id.code',store=True)
    
    def init(self):
        self._cr.execute("select 1 from information_schema.constraint_column_usage where table_name = 'hr_allowance' and constraint_name = 'hr_allowance_code_uniq'")
        if self._cr.rowcount:
            self._cr.execute("ALTER TABLE hr_allowance DROP CONSTRAINT hr_allowance_code_uniq")

    @api.constrains('allowance_config_id', 'employee_id', 'effective_date')
    def check_duplicate_record(self):
        for alw in self:
            if alw.allowance_config_id and alw.employee_id and alw.effective_date:
                domain = [('employee_id', '=', self.employee_id.id),
                          ('allowance_config_id', '=', self.allowance_config_id.id),
                          ('effective_type', '=', self.effective_type),
                          ('id', '!=', self.id)]
                if self.search(domain).filtered(lambda r: r.effective_date.month == alw.effective_date.month and r.effective_date.year == alw.effective_date.year):
                    raise ValidationError(_('Duplicate Record!!!'))
