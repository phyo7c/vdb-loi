{
    'name': 'Attendance Raw',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """

Attendance Raw
    """,
    'depends': ['base',
                'hr',
                'resource',
                'hr_attendance_ext'],
    'data': [
            'data/attendance_raw_data.xml',
            'security/ir.model.access.csv',
            'views/hr_attendance_raw_view.xml',
            'views/hr_employee_view.xml',
            'wizard/attendance_wizard.xml'
    ],    
    'installable': True,
    'auto_install': False,
}
