{
    'name': 'Contract',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'hr_contract',
    'website': 'http://7thcomputing.com',
    'description': """

Contract
    """,
    'depends': ['base',
                'hr_contract',
                'hr_contract_reports',
                'job_grade',
                ],
    'data': [
            'security/security.xml',
            'views/hr_contract_view.xml',
            'views/hr_contract_employee_report.xml',

    ],    
    'installable': True,
    'auto_install': False,
}
