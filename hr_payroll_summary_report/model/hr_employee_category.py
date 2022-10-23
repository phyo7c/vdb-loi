from odoo import fields, models


class EmployeeCategory(models.Model):
    _inherit = "hr.employee.category"

    tag_code = fields.Char(string="Code", required=True)
