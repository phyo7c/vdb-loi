from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tax_exemption_spouse = fields.Boolean('Tax Exemption for Spouse')
    father_name = fields.Char('Father Name')
    tax_exemption_father = fields.Boolean('Tax Exemption for Father')
    mother_name = fields.Char('Mother Name')
    tax_exemption_mother = fields.Boolean('Tax Exemption for Mother')
    pre_income_total = fields.Float('Previous Income Total')
    pre_tax_paid = fields.Float('Previous Tax Paid')
    financial_year = fields.Many2one('account.fiscal.year', string='Financial Year')
    insurance_amt = fields.Float(string='Insurance Amount')

