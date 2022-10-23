from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    managing_director_id = fields.Many2one('hr.employee', 'Managing Director')

