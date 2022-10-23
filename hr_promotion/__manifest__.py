{
    'name': 'Promotions',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Recruitment',
    'website': 'http://7thcomputing.com',
    'description': """

Promotions
    """,
    'depends': ['base',
                'hr',
                'hr_contract','salary_level','job_grade'],
    'data': [
            'data/data.xml',
            'security/ir.model.access.csv',
            'views/hr_promotion_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
