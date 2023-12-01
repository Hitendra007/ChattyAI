from asgiref.sync import sync_to_async

from .database_querries.when_withdraw_sql import sql_when_withdraw
from datetime import timedelta, datetime

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"

def ordinal(n):
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n)

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
    results = sql_when_withdraw(emp_id)
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
            return f'''Berdasarkan informasi terkini dari HR Anda, gaji Anda dapat diakses antara tanggal {start_date} hingga {end_date} siklus ini. Di luar rentang waktu tersebut, Anda tidak dapat menarik uang. Silakan hubungi departemen SDM Anda jika Anda memiliki pertanyaan lebih lanjut tentang perubahan tanggal siklus.'''
    except:
        return "Silakan hubungi departemen SDM Anda jika Anda memiliki pertanyaan lebih lanjut tentang perubahan tanggal siklus."
