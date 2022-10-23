{
    'name': 'HR Employee Movement Report',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
HR Employee Movement Report
    """,
    'depends': ['base',
                'hr'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_employee_movement_wizard.xml',

    ],
    'installable': True,
    'auto_install': False,
}