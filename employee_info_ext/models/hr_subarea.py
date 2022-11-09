from odoo import models, fields, api, _


class HrSubarea(models.Model):
    _name = 'hr.subarea'

    name = fields.Char('Name')