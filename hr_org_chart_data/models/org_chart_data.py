from odoo import tools
from odoo import models, fields

class HROrgChartData(models.Model):
    _name = "hr.org.chart.data"
    _description = "Organizational Chart Data"
    _auto = False
    id = fields.Integer('Sequence', readonly=True)
    level = fields.Integer('Level', readonly=True)
    record_id = fields.Integer('Record ID', readonly=True)
    data_type = fields.Char('Data Type', readonly=True)
    name = fields.Char('Name', readonly=True)
    employee_name = fields.Char('Employee Name', readonly=True)
    job_title = fields.Char('Job Title', readonly=True)
    parent_id = fields.Integer('Parent ID', readonly=True)
    parent_type = fields.Char('Parent Type', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        select_qry = """
        WITH
            hr_org_dummy AS (
        SELECT b.id,
    b.record_id,
    b.level,
    b.data_type,
    b.name,
    b.employee_name,
    b.job_title,
    b.parent_id,
    b.parent_type
   FROM ( SELECT row_number() OVER (ORDER BY a.level) AS id,
            a.id AS record_id,
            a.level,
            a.data_type,
            a.name,
            a.employee_name,
            a.job_title,
            a.parent_id,
            a.parent_type
           FROM ( SELECT rc.id,
                    1 AS level,
                    'group_company'::character varying AS data_type,
                    rc.name,
                    he.name AS employee_name,
                    hj.name AS job_title,
                    0 AS parent_id,
                    ''::character varying AS parent_type
                   FROM res_company rc,
                    hr_employee he,
                    hr_job hj
                  WHERE rc.managing_director_id = he.id AND he.job_id = hj.id AND rc.id = 1
                UNION ALL
                ( SELECT rc.id,
                    2 AS level,
                    'company'::character varying AS data_type,
                    rc.name,
                    he.name AS employee_name,
                    hj.name AS job_title,
                    1 AS parent_id,
                    'group_company'::character varying AS parent_type
                   FROM res_company rc,
                    hr_employee he,
                    hr_job hj
                  WHERE rc.managing_director_id = he.id AND he.job_id = hj.id
                  AND rc.id!=1
                  ORDER BY rc.name)
                UNION ALL
                ( SELECT rb.id,
                    3 AS level,
                    'branch'::character varying AS data_type,
                    rb.name,
                        CASE
                            WHEN he.name IS NULL THEN '<p style="color:#8B0000;">**VACCANT**</p>'::character varying
                            ELSE he.name
                        END AS employee_name,
                        CASE
                            WHEN hj.name IS NULL THEN ''::character varying
                            ELSE hj.name
                        END AS job_title,
                    rb.company_id AS parent_id,
                    'company'::character varying AS parent_type
                   FROM res_branch rb
                     LEFT JOIN hr_employee he ON rb.manager_id = he.id
                     LEFT JOIN hr_job hj ON he.job_id = hj.id
                  ORDER BY rb.name)
                UNION ALL
                select id,level,data_type,name,case when employee_name is not null then employee_name 
                else ''::character varying--'<p style="color:red;">vacant</p>'::character varying 
                end as employee_name,job_title,parent_id,parent_type
                from
                ( SELECT hd.id,
                    4 AS level,
                    'department'::character varying AS data_type,
                    hd.name,
                    case when hd.manager_id is null then ( SELECT hr_employee.name
                                                            FROM hr_employee
                                                            WHERE hr_employee.active = true AND hr_employee.company_id = hd.company_id AND hr_employee.job_id = hd.job_id AND hr_employee.department_id=hd.id
                                                            LIMIT 1) 
                    else he.name END AS employee_name,
                    case when hj.name is not null then hj.name
                    else ''::character varying end AS job_title,
                    --else '<p style="color:#8B0000;">**VACCANT**</p>'::character varying end AS job_title,
                    hd.branch_id AS parent_id,
                        CASE
                            WHEN hd.parent_id IS NULL THEN 'branch'::character varying
                            ELSE 'department'::character varying
                        END AS parent_type
                   FROM hr_department hd
                     LEFT JOIN hr_job hj ON hd.job_id = hj.id
                     LEFT JOIN hr_employee he ON hd.manager_id = he.id
                  --WHERE hd.active = true AND hd.parent_id IS NULL AND hd.job_id is not null AND hd.company_id IS NOT NULL)AA
                  WHERE hd.active = true AND hd.parent_id IS NULL AND hd.company_id IS NOT NULL)AA
                UNION ALL
                ( SELECT hd.id,
                    4 AS level,
                    'department'::character varying AS data_type,
                    hd.name,
                    case when hd.manager_id is null and ( SELECT hr_employee.name
                                                          FROM hr_employee
                                                          WHERE hr_employee.active = true AND hr_employee.company_id = hd.company_id AND hr_employee.job_id = hd.job_id
                                                          LIMIT 1 ) is not null then 
                                                          ''::character varying
                                                          ---( SELECT hr_employee.name
                                                          ---                       FROM hr_employee
                                                          ---                       WHERE hr_employee.active = true AND hr_employee.company_id = hd.company_id AND hr_employee.job_id = hd.job_id
                                                          ---                       LIMIT 1 )
                    when hd.manager_id is not null then (select hr_employee.name
                                                        from hr_employee
                                                        where hr_employee.active=true
                                                        and hr_employee.id=hd.manager_id) 
                    else ''::character varying END AS employee_name,
                    hj.name AS job_title,
                        CASE
                            WHEN hd.parent_id IS NULL THEN hd.branch_id
                            ELSE hd.parent_id
                        END AS parent_id,
                        CASE
                            WHEN hd.parent_id IS NULL THEN 'branch'::character varying
                            ELSE 'department'::character varying
                        END AS parent_type
                   FROM hr_department hd
                     LEFT JOIN hr_job hj ON hd.job_id = hj.id
                     LEFT JOIN hr_employee he ON hd.manager_id = he.id
                  WHERE hd.active = true AND hd.parent_id IS NOT NULL AND hd.company_id IS NOT NULL
                  ORDER BY hd.name)
                UNION ALL
                ( SELECT DISTINCT he.id,
                    5 AS level,
                    'employee'::character varying AS data_type,
                    CASE WHEN he.resign_date IS NULL THEN he.name                            
                            ELSE he.name || ' (Resign)'::character varying
                        END AS name,
                    CASE WHEN he.resign_date IS NULL THEN he.name                            
                            ELSE he.name || ' (Resign)'::character varying
                        END AS employee_name,
                    hj.name AS job_title,
                        he.department_id as parent_id,
                        'department'::character varying AS parent_type
                   FROM hr_employee he,
                    hr_job hj
                  WHERE he.job_id = hj.id AND he.active = true AND he.id not in(select manager_id from hr_department where manager_id is not null) AND NOT (he.id IN ( SELECT res_branch.manager_id
                           FROM res_branch
                          WHERE res_branch.manager_id IS NOT NULL))
                  ORDER BY name)
                UNION ALL
                ( SELECT DISTINCT he.id,
                    6 AS level,
                    'employee'::character varying AS data_type,
                    he.name,
                    he.name AS employee_name,
                    hj.name AS job_title,
                        he.parent_id as parent_id,
                        'employee'::character varying AS parent_type
                   FROM hr_employee he,
                    hr_job hj
                  WHERE he.job_id = hj.id AND he.active = true AND he.id not in(select manager_id from hr_department where manager_id is not null) AND parent_id is not null
                  ORDER BY he.name)
                UNION ALL
                (
                    select DISTINCT -1 id,
                    7 AS level,
                    'employee'::character varying AS data_type,
                    ''::character varying as name,
                    CASE
                            WHEN hd.manager_id IS NOT NULL and hd.job_id is not null and
                             ( SELECT hr_employee.name
                                                            FROM hr_employee
                                                            WHERE hr_employee.active = true AND hr_employee.id = hd.manager_id
                                                            LIMIT 1) is null THEN ''::character varying
                            WHEN hd.manager_id IS NOT NULL and hd.job_id is not null THEN concat('<p style="color:red;">vacant</p>','(',line.expected_new_employee,')')::character varying
                            WHEN hd.job_id is not null and hd.manager_id IS null  THEN ''::character varying
                            WHEN hd.job_id is null THEN concat('<p style="color:red;">vacant</p>','(',line.expected_new_employee,')')::character varying                            
                        END AS employee_name,
                    hj.name AS job_title,
                    line.department_id as parent_id,
                    'department'::character varying AS parent_type
                    from job_line line left join hr_job hj
                    on line.job_id=hj.id
                    left join hr_department hd on line.job_id=hd.job_id and line.department_id=hd.id
                    where hj.state='recruit'
                    --and line.expected_new_employee > 0
                    and line.total_employee > (select count(id) from hr_employee where job_id=line.job_id and company_id=line.company_id 
                    and branch_id=line.branch_id and department_id=line.department_id and active='t' and resign_date is null)
                    and line.company_id is not null 
                    and line.department_id is not null 
                    and line.branch_id is not null
                )
                ) a
          ORDER BY a.level, a.data_type, a.parent_id, a.id) b
  ORDER BY b.id ) 
  select * from hr_org_dummy where id not in (select id from hr_org_dummy 
where level=7 and employee_name='') 
--and parent_id in(select record_id from hr_org_dummy where employee_name='' and level=4 and job_title is not null))
        """
        return select_qry

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
        