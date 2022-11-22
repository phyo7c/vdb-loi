# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'PaThaKha Py3o Report',
    'version': '15.0.1.0.0',
    'category': 'HR',
    'license': 'AGPL-3',
    'summary': 'PaThaKha Py3o Report',
    'description': """
PaThaKha Py3o Report
===================

This module adds a sample py3o invoice report.

This module has been written by 7th Computing
<info@7thcomputing.com>.
    """,
    'author': '7th Computing',
    'depends': [
        'report_py3o_fusion_server','hr','account'],
    'data': [
        'views/report_pathaka.xml',
        'report.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'pathaka_py3o_report/static/src/scss/report_pathaka.scss',
        ],
    },
    'installable': True,
}

