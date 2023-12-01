from asgiref.sync import sync_to_async
from django.db import connection
from .database_querries.how_much_salary_sql import sql_how_much_salary, sql_accural
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"



def format_as_idr(amount):
    # Convert to string and reverse the string for easier processing
    amount_str = str(amount)[::-1]

    # Insert a comma after every third digit
    chunks = [amount_str[i:i + 3] for i in range(0, len(amount_str), 3)]
    amount_with_commas = ','.join(chunks)[::-1]

    return f"Rp{amount_with_commas}"


@sync_to_async
def how_much_salary(emp_id):

    results = sql_how_much_salary(emp_id)
    accural = sql_accural(emp_id)
    for res in results:
        print(res)
    print("------------------")
    for acc in accural:
        print(acc)
    if results:
        salary_amount = results[0]
        max_withdrawal_amount = results[1]
        max_amount_per_transaction = results[2]
        acc_salary = format_as_idr(int(accural[0]))
        used_balance = format_as_idr(int(accural[1]))
        avail_balance = format_as_idr(int(accural[2]))
        capped_amount_percentage = 0
        if salary_amount is None:
            return "Please reach out to your HR department"

        elif salary_amount and max_withdrawal_amount is not None:
            salary_amount = int(salary_amount)
            max_withdrawal_amount = int(max_withdrawal_amount)
            capped_amount_percentage = int((max_withdrawal_amount / salary_amount) * 100)

            salary_amount= format_as_idr(salary_amount)
            max_withdrawal_amount = format_as_idr(max_withdrawal_amount)

            if max_amount_per_transaction is not None:
                max_amount_per_transaction = int(max_amount_per_transaction)
                max_amount_per_transaction = format_as_idr(max_amount_per_transaction)

                return f'''Berdasarkan data terbaru yang kami dapatkan dari HRD anda, gaji anda adalah {salary_amount}. Per bulan anda dapat menarik nominal {max_withdrawal_amount}
                Per transaksi, anda dapat menarik uang sebesar {max_amount_per_transaction}
                Mulai hari ini, dalam siklus gaji saat ini, Anda telah memperoleh {acc_salary}, dan Anda membelanjakan {used_balance} dan tersisa {avail_balance} yang dapat Anda gunakan untuk bertransaksi.
                Jika ada perubahan nominal gaji, harap hubungi tim expert kami untuk membantu anda {whatsapp_chat_support_url}”.'''
            else:
                return f'''Berdasarkan data terbaru yang kami dapatkan dari HRD anda, gaji anda adalah {salary_amount}. Per bulan anda dapat menarik nominal {max_withdrawal_amount}.'''

        elif salary_amount:
                f'''Berdasarkan data terbaru yang kami terima dari departemen HR Anda, gaji Anda adalah {salary_amount}. Untuk informasi lebih lanjut, silakan hubungi Departemen HR Anda.'''

        else:
            return f'''Silakan hubungi Departemen HR Anda.'''
        # capped_amount_percentage = int((max_withdrawal_amount / salary_amount) * 100)
        # if max_amount_per_transaction is not None:
        #     return f'''Based on the latest data we received from your HR department, your salary is {salary_amount}. You can withdraw up to {capped_amount_percentage}% of your salary per month, which is equivalent to {max_withdrawal_amount}.
        #     Per transaction, you can withdraw {max_amount_per_transaction}.If there’s any amount changes, please reach out to your HR Department for confirmation.'''
        # if salary_amount:
        #      return f'''Based on the latest data we received from your HR department, your salary is {salary_amount}. You can withdraw up to {capped_amount_percentage}% of your salary per month, which is equivalent to {max_withdrawal_amount}.'''
        # else:
        #     return f'''Please reach out to your HR Department.'''


# @sync_to_async
# def how_much_salary(emp_id):
#
#     results = sql_how_much_salary(emp_id)
#     accural = sql_accural()
#     for res in results:
#         print(res)
#     if results:
#         salary_amount = results[0]
#         max_withdrawal_amount = results[1]
#         max_amount_per_transaction = results[2]
#         acc_salary = accural[0]
#         used_balance = accural[1]
#         avail_balance = accural[2];
#         capped_amount_percentage = 0
#         if salary_amount is None:
#             return "Please reach out to your HR department"
#
#         elif salary_amount and max_withdrawal_amount is not None:
#             salary_amount = int(salary_amount)
#             max_withdrawal_amount = int(max_withdrawal_amount)
#             capped_amount_percentage = int((max_withdrawal_amount / salary_amount) * 100)
#
#             salary_amount= format_as_idr(salary_amount)
#             max_withdrawal_amount = format_as_idr(max_withdrawal_amount)
#
#             if max_amount_per_transaction is not None:
#                 max_amount_per_transaction = int(max_amount_per_transaction)
#                 max_amount_per_transaction = format_as_idr(max_amount_per_transaction)
#
#                 return f'''Berdasarkan data terbaru yang kami terima dari departemen HR Anda, gaji Anda adalah {salary_amount}. Anda dapat menarik hingga {capped_amount_percentage}% dari gaji Anda per bulan, yang setara dengan {max_withdrawal_amount}.
#                 Per transaksi, Anda dapat menarik {max_amount_per_transaction}. Jika ada perubahan jumlah, harap hubungi Departemen HR untuk konfirmasi.'''
#             else:
#                 return f'''Berdasarkan data terbaru yang kami terima dari departemen HR Anda, gaji Anda adalah {salary_amount}. Anda dapat menarik hingga {capped_amount_percentage}% dari gaji Anda per bulan, yang setara dengan {max_withdrawal_amount}.
#                     Ini juga berlaku jika ada perubahan jumlah..'''
#
#         elif salary_amount:
#                 f'''Berdasarkan data terbaru yang kami terima dari departemen HR Anda, gaji Anda adalah {salary_amount}. Untuk informasi lebih lanjut, silakan hubungi Departemen HR Anda.'''
#
#         else:
#             return f'''Silakan hubungi Departemen HR Anda.'''
#         capped_amount_percentage = int((max_withdrawal_amount / salary_amount) * 100)
#         if max_amount_per_transaction is not None:
#             return f'''Based on the latest data we received from your HR department, your salary is {salary_amount}. You can withdraw up to {capped_amount_percentage}% of your salary per month, which is equivalent to {max_withdrawal_amount}.
#             Per transaction, you can withdraw {max_amount_per_transaction}.If there’s any amount changes, please reach out to your HR Department for confirmation.'''
#         if salary_amount:
#              return f'''Based on the latest data we received from your HR department, your salary is {salary_amount}. You can withdraw up to {capped_amount_percentage}% of your salary per month, which is equivalent to {max_withdrawal_amount}.'''
#         else:
#             return f'''Please reach out to your HR Department.'''
#
