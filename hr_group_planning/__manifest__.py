{
    'name': 'HR Group Planning',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee,Planning',
    'website': 'http://7thcomputing.com',
    'description': """
HR Group Planning
    """,
    'depends': ['base',
                'hr',
                'planning',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_group_view.xml',
        'wizard/planning_import_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}