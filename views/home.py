from flask import Blueprint, request, render_template, redirect, url_for
from datetime import datetime

from objects import Session, Manga, MangaType
from exceptions import (FieldValidationError, UserStateError,
                        InvalidUsernameError, InvalidPasswordError,
                        UsernameUsedError, EmailUsedError)
from utils import auth
from utils.auth import Context
from utils.web import mflash, time_str, time_ago_past

bp = Blueprint("home", __name__)


@bp.route("/", methods=["GET"])
def index():
    ctx = Context()
    manga = [{
        "name": "all",
        "display_name": "All",
        "active": True,
        "items": Manga.latest()
    }]
    for t in MangaType.all():
        manga.append({
            "name": t.name,
            "display_name": t.display_name,
            "active": False,
            "items": t.latest()
        })
    video = [{
        "name": "all",
        "display_name": "All",
        "active": True,
        "items": []
    }]
    return ctx.reply(render_template("home.html", ctx=ctx,
                                     manga_categories=manga, video_categories=video))


@bp.route("/about", methods=["GET"])
def about():
    ctx = Context()
    return ctx.reply(render_template("base.html", ctx=ctx))


@bp.route("/search", methods=["POST"])
def search():
    ctx = Context()
    return ctx.reply(render_template("base.html", ctx=ctx))
