{
    'name': 'Employee Tax Dependent',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
Employee Tax Dependent
    """,
    'depends': ['base',
                'hr',
                'account_accountant',
                ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
