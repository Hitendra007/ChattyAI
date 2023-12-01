
from django.db import connection

def sql_how_much_salary(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT "salaryAmount", "maxWithdrawalAmount", "maxAmountPerTransaction" 
            FROM gg_salary_profile 
            WHERE "employeeId" = {employee_id};
        """)
        results = cursor.fetchone()
        return results
def sql_accural(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
        SELECT "accrualAmount", "usedBalance", "availableBalance" 
        FROM gg_daily_balance where "employeeId" = {employee_id} ORDER BY "createdAt" desc limit 1;""")
        results = cursor.fetchone()
        return results