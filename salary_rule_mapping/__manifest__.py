{
    'name': 'Salary Rule Mapping',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """
Salary Rule Mapping
    """,
    'depends': ['base',
                'hr_payroll',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/raw_salary_rule_view.xml',
        'views/salary_rule_mapping_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
