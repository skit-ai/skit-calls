from skit_calls.cli import process_date_filters, to_datetime
from datetime import date, datetime, timedelta
from skit_calls import constants as const
import pytz



def test_process_date_filters_recurring_offset():
    fake_start_date = to_datetime('2022-09-20')
    fake_end_date = to_datetime('2022-09-29')
    fake_start_date_offset_1 = -7
    fake_start_time_offset_2 = 1524
    fake_end_time_offset_2 = 1600
    
    start_date, end_date = process_date_filters(fake_start_date, fake_end_date, fake_start_date_offset_1)
    assert start_date == '2022-09-13T00:00:00+05:53'
    assert end_date == '2022-09-29T23:59:59+05:53'
    
    start_date, end_date = process_date_filters(start_time_offset=fake_start_time_offset_2, end_time_offset=fake_end_time_offset_2)
    assert start_date == (datetime.combine(date.today(), datetime.min.time()) + timedelta(
            days=0, hours=15, minutes=24
        )).replace(tzinfo=pytz.timezone(const.DEFAULT_TIMEZONE)).isoformat()
    assert end_date == (datetime.combine(date.today(), datetime.max.time()) + timedelta(
            days=0, hours=16, minutes=00
        )).replace(tzinfo=pytz.timezone(const.DEFAULT_TIMEZONE)).isoformat()

def test_process_date_filters_time_offset():
    fake_start_date = to_datetime('2022-12-28')
    fake_end_date = to_datetime('2022-12-28')
    fake_start_time_offset = 12
    fake_end_time_offset = 14
    
    start_date, end_date = process_date_filters(fake_start_date, fake_end_date, start_time_offset=fake_start_time_offset, end_time_offset=fake_end_time_offset)
    assert start_date == '2022-12-28T12:00:00+05:53'
    assert end_date == '2022-12-28T14:59:59+05:53'
    
def test_process_date_filters_normal():
    fake_start_date = to_datetime('2022-12-28')
    fake_end_date = to_datetime('2022-12-28')
    
    start_date, end_date = process_date_filters(fake_start_date, fake_end_date)
    assert start_date == '2022-12-28T00:00:00+05:53'
    assert end_date == '2022-12-28T23:59:59+05:53'

def test_process_date_filters_current():
    fake_start_date = 0
    fake_end_date = 0
    
    start_date, end_date = process_date_filters(fake_start_date, fake_end_date)
    assert start_date == (datetime.combine(date.today(), datetime.min.time())).replace(tzinfo=pytz.timezone(const.DEFAULT_TIMEZONE)).isoformat()
    assert end_date == (datetime.combine(date.today(), datetime.max.time())).replace(tzinfo=pytz.timezone(const.DEFAULT_TIMEZONE)).isoformat()
