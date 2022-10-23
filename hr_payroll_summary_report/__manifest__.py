{
    'name': 'HR Payroll Summary Report',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
HR Payroll Summary Report
    """,
    'depends': ['base',
                'hr',
                'hr_payroll', 'hr_contract',             
                'account',
                'account_accountant',
                'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_category_views.xml',
        'reports/report_payroll_summary_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}