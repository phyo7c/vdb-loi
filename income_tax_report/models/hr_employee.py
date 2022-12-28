from odoo import fields, models, tools, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def salary_by_code(self, payslip_lines, code):
        line = payslip_lines.filtered(lambda l: l.code == code)
        if line:
            return line.total
        else:
            return 0

    def get_net_salary_lines(self, employee, fiscal_year_id):
        employees = self.env['hr.employee'].browse(employee.id)
        fiscal_year = self.env['account.fiscal.year'].browse(fiscal_year_id)
        for emp in employees:
            res = []
            last_salary = 0
            last_mmk = 0
            previous_income_total = 0.00
            self.env.cr.execute(
                """select from_date,to_date,hp.id
                from
                (
                    select *,TO_CHAR(
                        TO_DATE (date_part('month',from_date)::text, 'MM'), 'Mon'
                        ) AS month_name,date_part('year', from_date) AS year_name
                    from 
                    (
                        select generate_series(date_from,date_to, '1 month'::interval)::date from_date,
                        (date_trunc('month', generate_series(date_from,date_to, '1 month'::interval)::date) + interval '1 month' - interval '1 day')::date to_date
                        from account_fiscal_year 
                        where id=%s
                    )A
                )B
                left join hr_payslip hp on (B.from_date=hp.date_from and B.to_date=hp.date_to)
                where hp.employee_id=%s
                order by hp.date_to limit 1;""",
                (fiscal_year.id, emp.id,))
            first_payslip = self.env.cr.fetchall()
            if first_payslip:
                for slip in first_payslip:
                    payslip = self.env['hr.payslip'].search([('id', '=', slip[2])])
                    if payslip:
                        previous_income_total = self.salary_by_code(payslip.line_ids, 'PREI')
                    else:
                        previous_income_total = 0
                res.append({"type_of_income": "Previous Net Salary",
                            "net_salary": 0,
                            "months": 1.00,
                            "exchange_rate": 0.00,
                            "mmk": previous_income_total,
                            })
            self.env.cr.execute(
                """select *,concat(month_name,' ',year_name,' Net Salary') full_name
                from
                (
                    select *,TO_CHAR(
                        TO_DATE (date_part('month',from_date)::text, 'MM'), 'Mon'
                        ) AS month_name,date_part('year', from_date) AS year_name
                    from 
                    (
                        select generate_series(date_from,date_to, '1 month'::interval)::date from_date,
                        (date_trunc('month', generate_series(date_from,date_to, '1 month'::interval)::date) + interval '1 month' - interval '1 day')::date to_date
                        from account_fiscal_year 
                        where id=%s
                    )A
                )B;""",
                (fiscal_year.id,))
            generated_months = self.env.cr.fetchall()
            currency_rate = 0
            if generated_months:
                for month in generated_months:
                    payslip = self.env['hr.payslip'].search([('date_from', '=', month[0]),('date_to', '=', month[1]),('employee_id', '=', emp.id)],limit=1)
                    if payslip:
                        currency_rate = payslip.currency_rate
                        net_salary = self.salary_by_code(payslip.line_ids, 'NETUSD')
                        last_salary = self.salary_by_code(payslip.line_ids, 'NMIUSD')
                        mmk = self.salary_by_code(payslip.line_ids, 'GROSS')
                        last_mmk = last_salary * currency_rate
                    else:
                        net_salary = last_salary
                        mmk = last_mmk
                    res.append({"type_of_income": month[4],
                                "net_salary": net_salary,
                                "months": 1.00,
                                "exchange_rate": currency_rate,
                                "mmk": mmk,
                                })
        return res

    def get_annual_total_income(self, employee, fiscal_year_id, code):
        fiscal_year = self.env['account.fiscal.year'].browse(fiscal_year_id)
        self.env.cr.execute(
            """select from_date,to_date,hp.id
            from
            (
                select *,TO_CHAR(
                    TO_DATE (date_part('month',from_date)::text, 'MM'), 'Mon'
                    ) AS month_name,date_part('year', from_date) AS year_name
                from 
                (
                    select generate_series(date_from,date_to, '1 month'::interval)::date from_date,
                    (date_trunc('month', generate_series(date_from,date_to, '1 month'::interval)::date) + interval '1 month' - interval '1 day')::date to_date
                    from account_fiscal_year 
                    where id=%s
                )A
            )B
            left join hr_payslip hp on (B.from_date=hp.date_from and B.to_date=hp.date_to)
            where hp.employee_id=%s
            order by hp.date_to desc limit 1;""",
            (fiscal_year.id,employee.id,))
        last_payslip = self.env.cr.fetchall()
        if last_payslip:
            for slip in last_payslip:
                payslip = self.env['hr.payslip'].search([('id', '=', slip[2])])
                if payslip:
                    amount = self.salary_by_code(payslip.line_ids, code)
                else:
                    amount = 0
        return {
            "amount": amount,
        }

    def get_twenty_percent_exemption(self, employee, total_amount):
        if total_amount * 0.2 >= 10000000:
            amount = 10000000
        else:
            amount = total_amount * 0.2
        return {
            "twenty_percent_exemption": amount,
        }

    def get_spouse_exemption(self, employee):
        amount = 0
        if employee.tax_exemption_spouse:
            amount = 1000000
        return {
            "spouse_exemption": amount,
        }

    def get_children_exemption(self, employee):
        amount = 0
        if employee.children > 0:
            amount = employee.children * 500000
        return {
            "children_exemption": amount,
        }

    def get_parent_exemption(self, employee):
        amount = 0
        if employee.tax_exemption_father:
            amount += 1000000
        if employee.tax_exemption_mother:
            amount += 1000000
        return {
            "parent_exemption": amount,
        }

    def get_ssb_amount(self, employee):
        amount = 6000 * 12
        return {
            "ssb_amount": amount,
        }

    def get_zero_percent_rate(self, total_taxable_income, limit_amount):
        if total_taxable_income > limit_amount:
            amount = limit_amount
        else:
            amount = total_taxable_income
        return {
            "amount": amount,
        }

    def get_five_percent_rate(self, total_taxable_income, limit_amount):
        zero_percent = self.get_zero_percent_rate(total_taxable_income, limit_amount)
        if total_taxable_income - zero_percent.get('amount',0) > limit_amount:
            amount = limit_amount
        else:
            amount = total_taxable_income - zero_percent.get('amount',0)
        return {
            "amount": amount,
        }

    def get_ten_percent_rate(self, total_taxable_income, limit_amount):
        zero_percent = self.get_zero_percent_rate(total_taxable_income, limit_amount)
        five_percent = self.get_five_percent_rate(total_taxable_income, limit_amount)
        if total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) > limit_amount:
            amount = limit_amount
        else:
            amount = total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0)
        return {
            "amount": amount,
        }

    def get_fifteen_percent_rate(self, total_taxable_income, limit_amount):
        zero_percent = self.get_zero_percent_rate(total_taxable_income, limit_amount)
        five_percent = self.get_five_percent_rate(total_taxable_income, limit_amount)
        ten_percent = self.get_ten_percent_rate(total_taxable_income, limit_amount)
        if total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) - ten_percent.get('amount',0) > limit_amount:
            amount = limit_amount
        else:
            amount = total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) - ten_percent.get('amount',0)
        return {
            "amount": amount,
        }

    def get_twenty_percent_rate(self, total_taxable_income, limit_amount):
        zero_percent = self.get_zero_percent_rate(total_taxable_income, limit_amount)
        five_percent = self.get_five_percent_rate(total_taxable_income, limit_amount)
        ten_percent = self.get_ten_percent_rate(total_taxable_income, limit_amount)
        fifteen_percent = self.get_fifteen_percent_rate(total_taxable_income, limit_amount)
        if total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) - ten_percent.get('amount',0) - fifteen_percent.get('amount',0) > limit_amount:
            amount = limit_amount
        else:
            amount = total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) - ten_percent.get('amount',0) - fifteen_percent.get('amount',0)
        return {
            "amount": amount,
        }

    def get_twenty_five_percent_rate(self, total_taxable_income):
        zero_percent = self.get_zero_percent_rate(total_taxable_income, 2000000)
        five_percent = self.get_five_percent_rate(total_taxable_income, 8000000)
        ten_percent = self.get_ten_percent_rate(total_taxable_income, 20000000)
        fifteen_percent = self.get_fifteen_percent_rate(total_taxable_income, 20000000)
        amount = total_taxable_income - zero_percent.get('amount',0) - five_percent.get('amount',0) - ten_percent.get('amount',0) - fifteen_percent.get('amount',0)
        return {
            "amount": amount,
        }

    def get_prev_income_tax(self, employee, fiscal_year_id):
        amount = 0
        fiscal_year = self.env['account.fiscal.year'].browse(fiscal_year_id)
        if employee.financial_year and employee.financial_year.id == fiscal_year.id:
            amount = employee.prev_tax_paid
        return {
            "amount": amount,
        }

    def get_income_tax_lines(self, employee, fiscal_year_id):
        employees = self.env['hr.employee'].browse(employee.id)
        fiscal_year = self.env['account.fiscal.year'].browse(fiscal_year_id)
        for emp in employees:
            res = []
            last_income_tax = 0
            previous_tax_paid = 0.00
            self.env.cr.execute(
                """select from_date,to_date,hp.id
                from
                (
                    select *,TO_CHAR(
                        TO_DATE (date_part('month',from_date)::text, 'MM'), 'Mon'
                        ) AS month_name,date_part('year', from_date) AS year_name
                    from 
                    (
                        select generate_series(date_from,date_to, '1 month'::interval)::date from_date,
                        (date_trunc('month', generate_series(date_from,date_to, '1 month'::interval)::date) + interval '1 month' - interval '1 day')::date to_date
                        from account_fiscal_year 
                        where id=%s
                    )A
                )B
                left join hr_payslip hp on (B.from_date=hp.date_from and B.to_date=hp.date_to)
                where hp.employee_id=%s
                order by hp.date_to limit 1;""",
                (fiscal_year.id, emp.id,))
            first_payslip = self.env.cr.fetchall()
            if first_payslip:
                for slip in first_payslip:
                    payslip = self.env['hr.payslip'].search([('id', '=', slip[2])])
                    if payslip:
                        previous_tax_paid = self.salary_by_code(payslip.line_ids, 'PRETP')
                    else:
                        previous_tax_paid = 0
            res.append({"name": "Previous Income Tax",
                        "amount": previous_tax_paid,
                        })
            self.env.cr.execute(
                """select *,concat(month_name,' ',year_name,' Income Tax') full_name
                from
                (
                    select *,TO_CHAR(
                        TO_DATE (date_part('month',from_date)::text, 'MM'), 'Mon'
                        ) AS month_name,date_part('year', from_date) AS year_name
                    from 
                    (
                        select generate_series(date_from,date_to, '1 month'::interval)::date from_date,
                        (date_trunc('month', generate_series(date_from,date_to, '1 month'::interval)::date) + interval '1 month' - interval '1 day')::date to_date
                        from account_fiscal_year 
                        where id=%s
                    )A
                )B;""",
                (fiscal_year.id,))
            generated_months = self.env.cr.fetchall()
            currency_rate = 0
            if generated_months:
                for month in generated_months:
                    payslip = self.env['hr.payslip'].search([('date_from', '=', month[0]),('date_to', '=', month[1]),('employee_id', '=', emp.id)],limit=1)
                    if payslip:
                        salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'PIT')])
                        payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', payslip.id),('salary_rule_id', '=', salary_rule.id)])
                        if payslip_line:
                            income_tax = payslip_line.total
                            last_income_tax = payslip_line.total
                    else:
                        income_tax = last_income_tax
                    res.append({"name": month[4],
                                "amount": income_tax,
                                })
        return res