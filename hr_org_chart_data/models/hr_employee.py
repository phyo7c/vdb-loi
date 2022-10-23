from odoo import fields, models, api, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    manager_job_id = fields.Many2one('hr.job', string='Manager Position')
