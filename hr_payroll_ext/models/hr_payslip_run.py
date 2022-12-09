from odoo import api, fields, models, _


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    tax_approval_no = fields.Char('Tax Approval No')
