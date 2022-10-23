from odoo import fields, models


class JobGrade(models.Model):    
    _name = 'job.grade'    
    _description = 'Job Grade'
    
    name = fields.Char(string='Name')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!')
    ]
