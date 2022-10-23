from odoo import api, fields, models, _
class HrEducation(models.Model):
    _name = 'hr.education'
    name=fields.Char(string="Name")
    education = fields.Char(string="Education")