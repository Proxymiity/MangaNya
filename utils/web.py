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


def gen_paginate_data(current, pages, base_path, margin=2,
                      prev_btn=True, next_btn=True,
                      first_btn=True, last_btn=True):
    to_gen = []
    for i in reversed(range(1, margin+1)):
        if current - i <= 0:
            continue
        to_gen.append(current - i)
    to_gen.append(current)
    for i in range(1, margin+1):
        if current + i > pages:
            continue
        to_gen.append(current + i)
    data = []
    if prev_btn:
        if current - 1 > 0:
            data.append(("«", base_path.format(current - 1), ""))
        else:
            data.append(("«", "#", "disabled"))
    if first_btn:
        if 1 not in to_gen:
            data.append((1, base_path.format(1), ""))
            data.append(("...", "#", "disabled"))
    for p in to_gen:
        if p == current:
            data.append((p, base_path.format(p), "active"))
            continue
        data.append((p, base_path.format(p), ""))
    if last_btn:
        if pages not in to_gen:
            data.append(("...", "#", "disabled"))
            data.append((pages, base_path.format(pages), ""))
    if next_btn:
        if current + 1 <= pages:
            data.append(("»", base_path.format(current + 1), ""))
        else:
            data.append(("»", "#", "disabled"))
    return data
