from asgiref.sync import sync_to_async
from django.db import connection
from .database_querries.zero_balance_sql import sql_zero_balace, employer_status, employee_status, get_balance
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"

@sync_to_async
def zero_balance(emp_id):
    results = sql_zero_balace(emp_id)
    employee_stat = employee_status(emp_id)
    employer_stat = employer_status(emp_id)
    avl_balance = get_balance(emp_id)

    salary = results[0]
    max_withdrawal = results[1]

    if salary is None or salary<=0:
        return f""" “Berdasarkan informasi terbaru yang kami dapatkan dari pihak HRD anda, gaji anda tercatat sebagai 0. 
        Hal ini menyebabkan saldo dan limit harian anda juga menjadi nol. Silakan hubungi HRD anda untuk informasi lebih lanjut.”"""

    elif max_withdrawal is None or max_withdrawal<=0:
        return f""" “Berdasarkan informasi terbaru yang kami dapatkan dari pihak HRD anda, maksimal penarikan saldo anda tercatat sebagai 0.
         Hal ini menyebabkan saldo dan limit harian anda juga menjadi nol. Silakan hubungi HRD anda untuk informasi lebih lanjut.”"""
    elif employer_stat and avl_balance==0:
        return f""" Saat ini perusahaan anda sedang tidak dapat melakukan penambahan gaji. Harap hubungi HRD anda untuk menjalankan transaksi kembali """
    elif employee_stat and avl_balance==0:
        return f"""Saat ini anda sedang tidak diperkenankan untuk mendapat gaji tambahan harian. Harap hubungi HRD anda untuk penjelasan lebih lanjut."""
    else:
        return f""" “Nampaknya sedang terjadi kendala pada sistem. Harap hubungi tim expert kami untuk membantu anda {whatsapp_chat_support_url}”"""
