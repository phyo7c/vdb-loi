from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_office = fields.Char(string='Tax Office')
    hr_head_id = fields.Many2one("hr.employee", string='HR Head')



