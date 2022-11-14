{
    'name': 'Personal Income Tax Report',
    'version': '1.1',
    'category': 'Human Resources/Employees',
    'sequence': 95,
    'summary': 'Personal Income Tax Report',
    'description': "",
    'website': 'https://www.7thcomputing.com',
    'depends': [
        'base',
        'hr',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/hr_employee_tax_report_view.xml',
        'reports/income_tax_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
