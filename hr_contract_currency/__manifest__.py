{
    'name': 'HR Contract Currency',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'hr_contract',
    'website': 'http://7thcomputing.com',
    'description': """
HR Contract Currency
    """,
    'depends': ['base',
                'hr_contract',
                'hr_contract_reports',
                'hr_payroll'
                ],
    'data': [
            'views/hr_contract_view_form.xml',
            'views/employee_payslip_view.xml',

    ],
    'installable': True,
    'auto_install': False,
}
