{
    'name': 'Company Extension',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Base',
    'website': 'http://7thcomputing.com',
    'description': """
Company Extension
    """,
    'depends': ['base',
                'hr',
                ],
    'data': [
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
