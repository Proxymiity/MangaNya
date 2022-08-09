from flask import Blueprint, request, render_template, redirect, url_for
from datetime import datetime

from objects import Session, Manga, MangaType
from exceptions import (FieldValidationError, UserStateError,
                        InvalidUsernameError, InvalidPasswordError,
                        UsernameUsedError, EmailUsedError)
from utils import auth
from utils.auth import Context
from utils.web import mflash, time_str, time_ago_past
from utils import tasks

bp = Blueprint("tasks", __name__)


@bp.route("/tasks/wait/<string:task>", methods=["GET"])
def wait(task):
    ctx = Context()

    t = tasks.get_task(task)
    if t[0] is True:  # task completed
        if t[1].get("_endpoint"):
            if t[1]["_endpoint"].startswith(("http://", "https://")):  # endpoint is an URL, redirect
                return ctx.reply(redirect(t[1]["_endpoint"]))
            return ctx.reply(redirect(url_for(t[1]["_endpoint"], **t[1]["_endpoint_kwargs"])))
        return ctx.reply(redirect(url_for("home.index")))
    elif t[0] is False:  # task running
        url = url_for("tasks.wait", task=task)
        meta = f'<meta http-equiv="refresh" content="1;url={url}" />'
        mflash(f"{t[1].get('_info', '<b>Processing</b> Please wait while we process your request.')} <br>"
               f"{t[1].get('_progress', 'No progress info available')} "
               f"{meta}", "info")
        return ctx.reply(render_template("base.html", ctx=ctx))
    else:  # no task
        mflash("<b>Task not found.</b> No tasks were found with this ID.", "danger")
        return ctx.reply(redirect(url_for("home.index")))
