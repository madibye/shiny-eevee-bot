from datetime import timedelta

def get_time_remaining_str(time_remaining: timedelta):
    if time_remaining.total_seconds() >= 86400:
        return f"{round(time_remaining.total_seconds() / 86400)} {'days' if time_remaining.total_seconds() >= 172800 else 'day'}"
    if time_remaining.total_seconds() >= 3600:
        return f"{round(time_remaining.total_seconds() / 3600)} {'hours' if time_remaining.total_seconds() >= 7200 else 'hour'}"
    if time_remaining.total_seconds() >= 60:
        return f"{round(time_remaining.total_seconds() / 60)} {'minutes' if time_remaining.total_seconds() >= 120 else 'minute'}"
    return f"{round(time_remaining.total_seconds())} {'seconds' if time_remaining.total_seconds() >= 2 else 'second'}"
