"""Small date helpers shared across pages (no Streamlit)."""
from datetime import date


def first_of_month(d: date) -> date:
    return d.replace(day=1)


def shift_month(month: date, delta: int) -> date:
    """First day of the month `delta` months away from `month`."""
    idx = month.year * 12 + (month.month - 1) + delta
    return date(idx // 12, idx % 12 + 1, 1)
