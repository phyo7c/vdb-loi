{
    'name': 'Gulf Petrol Payroll',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'website': 'http://7thcomputing.com',
    'description': """
Gulf Petrol Payroll
    """,
    'depends': ['base',
                'hr_payroll',
                'hr_contract',
            ],
    'data': [
            'data/payroll_structure_data.xml',
            'data/salary_rule_data.xml',
            'data/payslip_input_type_data.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
}
