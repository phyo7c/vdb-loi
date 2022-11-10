{
    'name': 'HR Payroll Extension',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """
HR Payroll Extension
    """,
    'depends': ['base',
                'hr_payroll',
                'hr_contract_currency'
                ],
    'data': [
            'views/hr_payroll_rule_view.xml',
            'views/hr_payslip_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
