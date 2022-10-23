{
    'name': 'Public Holidays',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Leave',
    'website': 'http://7thcomputing.com',
    'description': """

Public Holidays
    """,
    'depends': ['base','hr','hr_holidays'],
    'data': [
            'security/ir.model.access.csv',
            'views/hr_public_holidays_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
