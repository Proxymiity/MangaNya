from flask import Blueprint, render_template
from math import ceil

from objects import Manga, MangaType
from utils.auth import Context
from utils.web import gen_paginate_data

bp = Blueprint("manga", __name__)


@bp.route("/manga/browse/<string:category>")
@bp.route("/manga/browse/<string:category>/<int:page>")
def browse(category, page=1):
    ctx = Context()
    count = Manga.count() if category == "all" else Manga.count(type_=category)
    pages = ceil(count / 50)
    pagination = gen_paginate_data(page, pages, f"/manga/browse/{category}/{{}}")
    offset = (page - 1) * 50
    manga = [{
        "name": "all",
        "display_name": "All",
        "active": category == "all",
        "items": Manga.latest(offset=offset) if category == "all" else [],
    }]
    for t in MangaType.all():
        manga.append({
            "name": t.name,
            "display_name": t.display_name,
            "active": category == t.name,
            "items": t.latest(offset=offset) if category == t.name else [],
        })
    return ctx.reply(render_template("manga_list.html", ctx=ctx, title=category.capitalize(),
                                     manga_categories=manga, pagination=pagination))
