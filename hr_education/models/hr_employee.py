from odoo import api, fields, models, _
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    education = fields.Many2one('hr.education', string='Education')


