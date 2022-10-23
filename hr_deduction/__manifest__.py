{
    'name': 'Deduction',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """

Deduction
    """,
    'depends': ['base','hr_payroll'],
    'data': [
            'views/hr_deduction_view.xml',
            'security/ir.model.access.csv',
    ],    
    'installable': True,
    'auto_install': False,
}
