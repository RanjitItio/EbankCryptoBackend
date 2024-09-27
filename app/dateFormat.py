from datetime import datetime, timedelta
import calendar



@staticmethod
def get_date_range(currenct_time_date: str):
    now = datetime.now()

    if currenct_time_date == 'Today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif currenct_time_date == 'Yesterday':
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
    elif currenct_time_date == 'ThisWeek':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif currenct_time_date == 'ThisMonth':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif currenct_time_date == 'PreviousMonth':
        first_day_last_month = (now.replace(day=1) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = first_day_last_month.replace(day=1)
        end_date = first_day_last_month.replace(day=calendar.monthrange(first_day_last_month.year, first_day_last_month.month)[1], hour=23, minute=59, second=59)
    else:
        raise ValueError(f"Unsupported date range: {currenct_time_date}")
    
    return start_date, end_date