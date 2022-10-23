# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = "Group on Employee"
    _order = "name"

    name = fields.Char('Group Name', required=True)


class Employee(models.Model):
    _inherit = 'hr.employee'

    group_id = fields.Many2one('hr.employee.groups', string='Group')
    is_roaster = fields.Boolean("Roaster", default=False)


class Slot(models.Model):
    _inherit = 'planning.slot'

    check_date = fields.Date()
