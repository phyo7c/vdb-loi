from odoo import api, fields, models, _

class RawSalaryRule(models.Model):
    _name = 'raw.salary.rule'

    name = fields.Char('Name')