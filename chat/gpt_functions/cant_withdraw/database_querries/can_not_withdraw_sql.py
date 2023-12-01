
from django.db import connection

def sql_cant_withdraw(emp_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT gg_payment_cycle."firstWorkingDate"::DATE, 
                   gg_payment_cycle."endWorkingDate"::DATE, 
                   gg_salary_profile."numberOfLockPeriod", 
                   gg_salary_profile."withdrawalLockType",
                   gg_payment_cycle."startWithdrawalDate"
            FROM gg_payment_cycle
            JOIN gg_salary_profile 
            ON gg_payment_cycle."salaryProfileId" = gg_salary_profile.id
            WHERE gg_payment_cycle."employeeId" = {emp_id} 
            ORDER BY gg_payment_cycle."createdAt" DESC 
            LIMIT 1;
        """)
        results = cursor.fetchone()
        return results
