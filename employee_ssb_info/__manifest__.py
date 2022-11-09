{
    'name': 'Employee SSB Info',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """

Employee SSB Info
    """,
    'depends': ['base',
                'hr',
                # 'contacts',
                ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
