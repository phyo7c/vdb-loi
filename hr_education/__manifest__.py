{
    'name': 'HR Education',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
HR Education Customization
    """,
    'depends': ['base',
                'hr',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_education_view.xml',
        'views/hr_employee_view.xml',

    ],
    'installable': True,
    'auto_install': False,
}