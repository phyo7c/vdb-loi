{
    'name': 'Attendance Customization',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """

Attendance Customization
    """,
    'depends': ['base', 'hr','resource','hr_attendance','hr_public_holiday'],
    'data': [
        'data/attendance_data.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
