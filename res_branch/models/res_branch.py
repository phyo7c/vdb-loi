from odoo import fields, models

class Branch(models.Model):    
    _name = 'res.branch'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Branch'

    code  = fields.Char(string='Code',tracking=True)
    name  = fields.Char(string='Name',tracking=True)
    company_id  = fields.Many2one('res.company', string='Company',tracking=True)
    analytic_account_id  = fields.Many2one('account.analytic.account', string='Analytic Account',tracking=True)
    manager_id = fields.Many2one('hr.employee', 'Branch Manager', tracking=True)
    ssb_office_no = fields.Char(string='SSB Office No',tracking=True)
    ssb_branch_name = fields.Char(string='SSB Branch Name',tracking=True)
    ssb_office_address = fields.Char(string='SSB Office Address',tracking=True)
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'code must be unique!')
    ]