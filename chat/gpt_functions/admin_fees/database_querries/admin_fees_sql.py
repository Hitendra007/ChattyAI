
from django.db import connection

def sql_admin_fees(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
                 SELECT "feeType", "fee" 
        FROM gg_salary_profile 
        WHERE "employeeId" = {employee_id}
        ORDER BY "createdAt" DESC LIMIT 1;
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

# def sql_getinfo(employee_id):
#     with connection.cursor() as cursor:
#         cursor.execute(f"""
#                         SELECT "label", "humanRequired", "nonGG"
#                         FROM chat_message LIMIT 1;
#                         """)
#         results = cursor.fetchone()
#         return results
