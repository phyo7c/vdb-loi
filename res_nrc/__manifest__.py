# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Customer NRC',
    'version': '1.0',
    'sequence': 14,
    'summary': 'NRC Myanmar',
    'description': """
Manage nrc
======================================
With this module for nrc.
    """,
    'author': '7thcomputing developers',
    'website': 'http://www.7thcomputing.com',
    'category': 'Employee',
    'depends': ['base', 'hr', 'contacts'],
    'data' : [
        'security/ir.model.access.csv',
        'data/res.nrc.region.csv',
        'data/res.nrc.prefix.csv',
        'data/res.nrc.type.csv',
        'views/res_partner_view.xml',
        'views/res_nrc_view.xml',
        'views/hr_employee_view.xml',
    ],
    'demo': [],
    'installable': True,
}
