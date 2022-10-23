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
                'hr_payroll',              
                'account',
                'account_accountant',
                'mail'],
    'data': [
        'security/ir.model.access.csv',
        
        'data/structure_rule.xml',
        'data/office_rule.xml',
        # 'views/res_branch_view.xml',
        # 'report/report_menu.xml',
        # 'report/yangon_payslip.xml',
        # 'report/header.xml',
        'views/hr_employee_view.xml',
        # 'views/employee_info.xml',
        # 'views/hr_allowance_view.xml',
        # 'views/hr_payroll_view.xml',
        # 'views/hr_public_holidays_view.xml',
        # 'views/ot_allowance_view.xml',

        
        
    ],    
    'installable': True,
    'auto_install': False,
}