from odoo import fields, models

class SalaryLevel(models.Model):    
    _name = 'salary.level'    
    _description = 'Salary Level'

    name = fields.Char(string='Name')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!')
    ]