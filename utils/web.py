from flask import Markup, flash
from datetime import datetime


def mflash(message, category):
    return flash(Markup(message), category)


def time_str(dt):
    return dt.strftime('%d/%m/%Y %H:%M:%S UTC')


def time_ago(dt):
    now = datetime.utcnow()
    if now <= dt:
        return "now"  # Prevents a database time drift from messing up frontend
    delta = now - dt
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d or h or m:
        if d or h:
            if d:
                return f"{d}d{h}h ago"
            return f"{h}h{m}m ago"
        return f"{m}m{s}s ago"
    return f"{s}s ago"
