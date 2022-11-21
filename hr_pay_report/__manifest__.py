{
    'name': 'HR Pay Report',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
HR Pay Report
    """,
    'depends': ['base',
                'hr',
                'hr_payroll', 'hr_contract',             
                'account',
                'account_accountant',
                'mail', 'employee_info_ext'],
    'data': [
        'security/ir.model.access.csv',
        'reports/pay_report_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}