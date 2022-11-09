from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    currency_not_convert = fields.Boolean(string='Currency not convert', default=False)