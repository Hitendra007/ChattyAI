from asgiref.sync import sync_to_async
from django.db import connection
from .database_querries.transaction_status_sql import sql_transaction_status
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"


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
