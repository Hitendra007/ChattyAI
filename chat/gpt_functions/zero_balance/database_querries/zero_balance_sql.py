from django.db import connection

def sql_zero_balace(emp_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT "salaryAmount", "maxWithdrawalAmount"
            FROM gg_salary_profile
            WHERE "employeeId"={emp_id} ORDER BY "createdAt" DESC LIMIT 1;
        """)
        results = cursor.fetchone()
        return results

def employer_status(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f'select status from gg_employer where status != \'active\' and id = (select "employerId" from gg_employee where id = {employee_id} )')
        employer_status = cursor.fetchone()
        return employer_status

def employee_status(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f'select status from gg_employee where status != \'active\' and id = {employee_id}')
        employee_status = cursor.fetchone()
        return employee_status

def get_balance(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
           SELECT "availableBalance" 
           FROM gg_daily_balance where "employeeId" = {employee_id} ORDER BY "createdAt" desc limit 1;""")
        results = cursor.fetchone()
        return results