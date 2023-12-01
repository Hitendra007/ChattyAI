from asgiref.sync import sync_to_async
from django.db import connection
from .database_querries.admin_fees_sql import sql_admin_fees
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"



def format_as_idr(amount):
    # Convert to string and reverse the string for easier processing
    amount_str = str(amount)[::-1]

    # Insert a comma after every third digit
    chunks = [amount_str[i:i + 3] for i in range(0, len(amount_str), 3)]
    amount_with_commas = ','.join(chunks)[::-1]
    return f"{amount_with_commas}"



@sync_to_async
def admin_fees(emp_id):

    results = sql_admin_fees(emp_id)

    # accural = sql_accural(emp_id)emp_id
    for res in results:
        print(res)
    print("------------------")
    if results:
        fee_type = results[0]
        fee_amount = format_as_idr(int(results[1]))

        if fee_type == 'FIXED':
            return f"""
                    1. Transaksi penarikan saldo gaji sebesar Rp {fee_amount} per transaksi penarikan.
                    2. Transaksi pembelian emas digital tidak dikenakan biaya admin 
                    3. Transaksi di menu pembayaran akan ditentukan oleh masing-masing provider pembayaran
                    """
        else:
            return  f"""
                    1. Transaksi penarikan saldo gaji sebesar {fee_amount}% per transaksi penarikan.
                    2. Transaksi pembelian emas digital tidak dikenakan biaya admin 
                    3. Transaksi di menu pembayaran akan ditentukan oleh masing-masing provider pembayaran
                    """
