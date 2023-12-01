from asgiref.sync import sync_to_async
from django.db import connection
from .database_querries.can_not_withdraw_sql import sql_cant_withdraw
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"

def ordinal(n):
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

def custom_date_format(dt):
    month_map = {
        'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
        'April': 'April', 'May': 'Mei', 'June': 'Juni',
        'July': 'Juli', 'August': 'Agustus', 'September': 'September',
        'October': 'Oktober', 'November': 'November', 'December': 'Desember'
    }
    return "{} {}".format(ordinal(dt.day), month_map[dt.strftime('%B')])


@sync_to_async
def can_not_withdraw(emp_id):
    with connection.cursor() as cursor:
            # Check if not within open cycle
        cursor.execute(f'select "isLockPeriod" from gg_daily_balance where "employeeId" = {emp_id} order by "createdAt" DESC LIMIT 1;')
        is_lock_period = cursor.fetchone()

        if is_lock_period and is_lock_period[0] == True:
            lock_period_status = "Employee is not in open cycle."
            results = sql_cant_withdraw(emp_id)

            if results:
                first_working_date, end_working_date, number_of_lock_period, withdrawal_lock_type, start_withdrawal_date = results
                if withdrawal_lock_type == 'FLEXIBLE':
                    start_date = first_working_date
                    end_date = end_working_date - timedelta(days=number_of_lock_period)
                elif withdrawal_lock_type == 'FIXED':
                    start_date = first_working_date
                    end_date = datetime(end_working_date.year, end_working_date.month, number_of_lock_period)
                else:
                    start_date = None
                    end_date = None
            try:
                if int(start_withdrawal_date) > 0:
                    if int(start_date.day) >= int(start_withdrawal_date):
                        start_date = datetime(end_date.year, end_date.month, int(start_withdrawal_date))
                    else:
                        start_date = datetime(start_date.year, start_date.month, int(start_withdrawal_date))
            except Exception as error:
                print("*****---> start_withdrawal_date", error)

            if start_date and end_date:
                start_date = custom_date_format(start_date)
                end_date = custom_date_format(end_date)
                return f"Saat ini anda sedang berada diluar periode penarikan gaji. Anda bisa menarik gaji pada tanggal {start_date} dan tanggal {end_date} setiap bulan."
        elif is_lock_period and is_lock_period[0] == False:
            lock_period_status = "Employee is in open cycle."

            # Check if employer is suspended
        cursor.execute(
                f'select status from gg_employer where status != \'active\' and id = (select "employerId" from gg_employee where id = {emp_id} )')
        employer_status = cursor.fetchone()

        if employer_status:
            employer_status = "Employer is suspended."
            return "Saat ini perusahaan anda sedang tidak dapat melakukan transaksi. Harap hubungi HRD anda untuk menjalankan transaksi kembali."
        else:
            employer_status = "Employer is not suspended."

            # Check if employee is suspended
        cursor.execute(f'select status from gg_employee where status != \'active\' and id = {emp_id}')
        employee_status = cursor.fetchone()

        if employee_status:
            employee_status = "Employee is suspended."
            return "Saat ini anda sedang tidak diperkenankan untuk melakukan transaksi. Harap hubungi HRD anda untuk penjelasan lebih lanjut."
        else:
            employee_status = "Employee is not suspended."
    return f"Nampaknya sedang terjadi kendala pada sistem. Harap hubungi tim expert kami untuk membantu anda {whatsapp_chat_support_url}."
