# Copyright (C) 2017 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Attendance Report",
    "version": "15.0.1.0.2",
    "license": "AGPL-3",
    "category": "Reporting",
    "author": "GRAP,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/reporting-engine",
    "depends": ["base", 'hr','resource'],
    "data": [
       'report/attendance_report.xml',
       "security/ir.model.access.csv",
    ],
    "demo": [],
    "installable": True,
    
}
