{
    'name': 'Allowance',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """

Allowance
    """,
    'depends': ['base','hr_payroll'],
    'data': [
            'views/hr_allowance_view.xml',
            'security/ir.model.access.csv',
            'views/ot_allowance_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
