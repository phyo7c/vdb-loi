{
    'name': 'Employee Attendance Early Out',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Employee',
    'website': 'http://7thcomputing.com',
    'description': """
Employee Attendance Early Out
    """,
    'depends': ['base',
                'hr_attendance',
                'res_branch',],
    'data': [
            'security/ir.model.access.csv',
            'views/hr_attendance_early_out_view.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
