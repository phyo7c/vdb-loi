{
    'name': 'Organizational Chart Data',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'HR',
    'website': 'http://7thcomputing.com',
    'description': """

Organizational Chart Data
    """,
    'depends': ['base', 'hr','job_grade','res_branch'],
    'data': [
            'security/ir.model.access.csv',
            'views/org_chart_data_view.xml',
            'views/res_company_view.xml',
            'views/hr_job_view.xml',
            'views/hr_department_view.xml',
            'views/hr_employee_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
