{
    'name': 'PaThaKha Report',
    'version': '1.1',
    'category': 'Human Resources/Employees',
    'sequence': 95,
    'summary': 'PaThaKha Report',
    'description': "",
    'website': 'https://www.7thcomputing.com',
    'depends': [
        'base',
        'hr',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/pathakha_report_wizard.xml',
        'reports/pathakha_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
