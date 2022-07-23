from flask import Markup, flash
from datetime import datetime
import timeago


def mflash(message, category):
    return flash(Markup(message), category)


def time_str(dt):
    return dt.strftime('%d/%m/%Y %H:%M:%S UTC')


def time_ago(dt):
    now = datetime.utcnow()
    return timeago.format(dt, now)


def time_ago_past(dt):
    now = datetime.utcnow()
    if now <= dt:
        return "now"  # Prevents a database time drift from messing up frontend
    return timeago.format(dt, now)
