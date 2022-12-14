{
    'name': 'Employee Info Ext',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """

Employee Info Extension
    """,
    'depends': ['base',
                'base_setup',
                'hr',
                'contacts',
                'employee_tax_dependent'
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/res_nrc_view.xml',
        # 'views/res_partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
