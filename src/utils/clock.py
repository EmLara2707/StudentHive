"""The app's one clock: Philippine time (Asia/Manila).

The server may run in any timezone (a cloud host is usually UTC, which is 8 hours
behind Manila), so nothing may call date.today() or datetime.now() directly:
"today" would be wrong for Manila users between 00:00 and 08:00. Use these instead.
No Streamlit."""
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    MANILA = ZoneInfo("Asia/Manila")
except Exception:  # no tz database on this host: the Philippines has no DST, so UTC+8 is exact
    MANILA = timezone(timedelta(hours=8), "PST")


def now_manila() -> datetime:
    """The current moment as a timezone-aware Manila datetime."""
    return datetime.now(MANILA)


def today_manila() -> date:
    """Today's date in Manila."""
    return now_manila().date()
