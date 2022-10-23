{
    'name': "Import Overtime Request",
    'version': "12.0.0.0",
    'summary': "This module helps you to import overtime request",
    'category': 'HR',
    'description': """
        Using this module overtime request is imported using excel sheets 
    """,
    'author': "7thcomputing",
    'website':"https://www.7thcomputing.com",
    'depends': ['base', 'hr_ot_request'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_ot_request.xml',        
    ],
    'demo': [],
    "license": "AGPL-3",
    'installable': True,
    'auto_install': False,
}
