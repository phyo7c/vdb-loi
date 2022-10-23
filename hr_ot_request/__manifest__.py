{
    'name': 'Overtime Request',
    'version': '1.0.0',
    'author': '7thcomputing',
    'license': 'AGPL-3',
    'category': 'Attendances',
    'website': 'http://7thcomputing.com',
    'description': """

Overtime Request
    """,
    'depends': ['base','hr','mail','res_branch','hr_holidays','hr_attendance_raw'
                ],
    'data': [
            'views/hr_ot_request_view.xml',
            'views/hr_ot_response_view.xml',
            'views/time_off_views.xml',
            'security/ir.model.access.csv',            
            'data/hr_ot_request.xml',
            'wizard/overtime_request_report.xml',
    ],    
    'installable': True,
    'auto_install': False,
}
