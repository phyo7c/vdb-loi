{
    'name': 'Leave Summary Request',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'TimeOff',
    'website': 'http://7thcomputing.com',
    'description': """

Leave Summary Request
    """,
    'depends': ['base', 'hr','hr_holidays'],
    'data': [
            'security/hr_security.xml',
            'security/ir.model.access.csv',
            'views/hr_leave_summary_request_view.xml',
            'views/hr_leave_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
