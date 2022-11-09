{
    'name': 'Raw Payslip',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """
Raw Payslip
    """,
    'depends': ['base',
                'hr_payroll',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/raw_payslip_view.xml',
        'wizards/import_payslip_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
