{
    'name': 'HR Payroll Customization',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
HR Payroll Customization
    """,
    'depends': ['base',
                'hr',
                'hr_payroll', 'hr_contract',             
                'account',
                'account_accountant',
                'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'reports/report_payroll_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}