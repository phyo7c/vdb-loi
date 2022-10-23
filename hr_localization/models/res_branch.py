from odoo import fields, models

class Branch(models.Model):    
    _name = 'res.branch'    
    _description = 'Branch'

    code  = fields.Char(string='Code')
    name  = fields.Char(string='Name')
    company_id  = fields.Many2one('res.company', string='Company')
    analytic_account_id  = fields.Many2one('account.analytic.account', string='Analytic Account')
    ssb_office_no = fields.Char(string='SSB Office No')
    ssb_branch_name = fields.Char(string='SSB Branch Name')
    ssb_office_address = fields.Char(string='SSB Office Address')
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'code must be unique!')
    ]