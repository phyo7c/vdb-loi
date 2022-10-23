{
    'name': 'HR Leave Carried Forward',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'TimeOff',
    'website': 'http://7thcomputing.com',
    'description': """
        HR Leave Carried Forward
    """,
    'depends': ['base','hr_holidays', 'hr_leave_auto_allocation'],
    'data': [
            'data/ir_cron_data.xml',
            'views/hr_leave_auto_allocation_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}