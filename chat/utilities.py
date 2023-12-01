from datetime import timedelta, datetime
from asgiref.sync import sync_to_async
from django.db import connection
from . gpt_functions.cant_withdraw.database_querries.can_not_withdraw_sql import sql_cant_withdraw
whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948&text&type=phone_number&app_absent=0"

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
def when_withdraw(emp_id):
    results = sql_cant_withdraw(emp_id)
    try:
        if results:
            first_working_date, end_working_date, number_of_lock_period, withdrawal_lock_type = results
            if withdrawal_lock_type == 'FLEXIBLE':
                start_date = first_working_date
                end_date = end_working_date - timedelta(days=number_of_lock_period)
            elif withdrawal_lock_type == 'FIXED':
                start_date = first_working_date
                end_date = datetime(end_working_date.year, end_working_date.month, number_of_lock_period)
            else:
                start_date = None
                end_date = None

        if start_date and end_date:
            start_date=custom_date_format(start_date)
            end_date=custom_date_format(end_date)
            return f'''Based on latest information from your HR, your salary can be accesed between {start_date} until {end_date} this cycle. Outside of those time range, you can not withdraw money. Please reach out to your HR department if you have further question about cycle date changes.'''
    except:
        return "Please reach out to your HR department if you have further question about cycle date changes."


@sync_to_async
def can_not_withdraw(emp_id):
    with connection.cursor() as cursor:
            # Check if not within open cycle
        cursor.execute(f'select "isLockPeriod" from gg_daily_balance where "employeeId" = {emp_id} order by "createdAt" DESC LIMIT 1;')
        is_lock_period = cursor.fetchone()

        if is_lock_period and is_lock_period[0] == True:
            lock_period_status = "Employee is not in open cycle."
            cursor.execute(f"""
                        SELECT gg_payment_cycle."firstWorkingDate"::DATE, 
                               gg_payment_cycle."endWorkingDate"::DATE, 
                               gg_salary_profile."numberOfLockPeriod", 
                               gg_salary_profile."withdrawalLockType" ,
                               gg_salary_profile."startWithdrawalDate"
                        FROM gg_payment_cycle
                        JOIN gg_salary_profile 
                        ON gg_payment_cycle."salaryProfileId" = gg_salary_profile.id
                        WHERE gg_payment_cycle."employeeId" = {emp_id} 
                        ORDER BY gg_payment_cycle."createdAt" DESC 
                        LIMIT 1;
                    """)
            results = cursor.fetchone()

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


@sync_to_async
def transaction_status(emp_id):
    with connection.cursor() as cursor:
        # Check if transaction time is under 15 minutes ago
        cursor.execute(f'select "createdAt" from gg_transaction where "employeeId" = {emp_id} order by "createdAt" DESC limit 1;')
        transaction_time = cursor.fetchone()

        if transaction_time and (datetime.now() - transaction_time[0]).total_seconds() < 900:
            transaction_status = "The transaction is still being processed. Please wait for 15 minutes and check if the transaction is still pending."
            return transaction_status
        else:
            transaction_status = None

        # Get distinct unsuccessful transaction IDs
        cursor.execute(f'select id from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\')order by "createdAt" DESC LIMIT 3;')
        transaction_ids = cursor.fetchall()

        if transaction_ids:
            no_of_tranx= len(transaction_ids)
            transaction_ids =', '.join([str(id[0]) for id in transaction_ids])
            transaction_ids_status = f"Kami menemukan {no_of_tranx} transaksi yang tidak berhasil dengan ID transaksi berikut: {transaction_ids}. Silakan hubungi dukungan pelanggan kami menggunakan {whatsapp_chat_support_url}"
            return transaction_ids_status
        else:
            transaction_ids_status = None

        # Check if no transaction found
        cursor.execute(f'select count(id) from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\');')
        transaction_count = cursor.fetchone()

        if transaction_count and transaction_count[0] == 0:
            no_transaction_status = f"Kami tidak menemukan transaksi yang tertunda. Silakan hubungi tim ahli kami dengan URL WhatsApp di bawah {whatsapp_chat_support_url}"
            return no_transaction_status
        else:
            no_transaction_status = None

    return f"Kami tidak menemukan transaksi yang tertunda. Silakan hubungi tim ahli kami dengan URL WhatsApp di bawah {whatsapp_chat_support_url}"
# def transaction_status(emp_id):
#     with connection.cursor() as cursor:
#         # Check if transaction time is under 15 minutes ago
#         cursor.execute(
#             f'select "createdAt" from gg_transaction where "employeeId" = {emp_id} order by "createdAt" DESC limit 1;')
#         transaction_time = cursor.fetchone()
#
#         if transaction_time and (datetime.now() - transaction_time[0]).total_seconds() < 900:
#             transaction_status = "The transaction is still being processed. Please wait for 15 minutes and check if the transaction is still pending."
#             return transaction_status
#         else:
#             transaction_status = None
#
#         # Get distinct unsuccessful transaction IDs
#         cursor.execute(
#             f'select id from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\')')
#         transaction_ids = cursor.fetchall()
#
#         if transaction_ids:
#             transaction_ids = ', '.join([str(id[0]) for id in transaction_ids])
#             transaction_ids_status = f"We found {len(transaction_ids)} transactions that are not successful with the followingtransaction IDs: {transaction_ids}. Please reach our customer support using {whatsapp_chat_support_url}"
#             return transaction_ids_status
#         else:
#             transaction_ids_status = None
#
#         # Check if no transaction found
#         cursor.execute(f'select count(id) from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\') order by "createdAt" DESC;')
#         transaction_count = cursor.fetchone()
#
#         if transaction_count and transaction_count[0] == 0:
#             no_transaction_status = f"We did not found any pending transaction. Please reach out to our expert team with the WhatsApp URL below {whatsapp_chat_support_url}"
#             return no_transaction_status
#         else:
#             no_transaction_status = None
#
#     return  f"We did not found any pending transaction. Please reach out to our expert team with the WhatsApp URL below {whatsapp_chat_support_url}"