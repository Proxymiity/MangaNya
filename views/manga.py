from flask import Blueprint, render_template, url_for, redirect
from math import ceil

from objects import Manga, MangaType, User
from objects.manga import state_name
from utils.auth import Context
from utils.web import gen_paginate_data, mflash
from utils.proxy import get_url
from utils import tasks

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


@bp.route("/m/<int:manga>")
def view(manga):
    ctx = Context()
    manga = Manga.from_id(manga)
    if manga is None:
        mflash("<b>Not Found.</b> The requested manga wasn't found.", "danger")
        return ctx.reply(redirect(url_for("home.index")))
    user = User.from_id(manga.uploader)
    return ctx.reply(render_template("manga.html", ctx=ctx, m=manga, u=user,
                                     state=state_name(manga.state),
                                     d_created=None, d_updated=None, d_sourced=None))


@bp.route("/m/<int:manga>/<string:method>")
@bp.route("/m/<int:manga>/<string:method>/<int:page>")
@bp.route("/m/<int:manga>/<string:method>/<string:filetype>")
def reader_dispatch(manga, method, page=1, filetype=None):
    ctx = Context()
    methods = ("r", "cr", "ir", "r-s", "ir-s", "dl", "dl-s")
    manga = Manga.from_id(manga)
    if manga is None:
        mflash("<b>Not found.</b> The requested manga wasn't found.", "danger")
        return ctx.reply(redirect(url_for("home.index")))
    # Check if method is supported
    if method not in methods:
        mflash("<b>Unknown method.</b> Viewing method wasn't found.", "danger")
        return ctx.reply(redirect(url_for("manga.view", manga=manga.id)))
    # Check if the request is a download request
    if method in ("dl", "dl-s"):
        return download_dispatch(ctx, manga, method, filetype)
    # Run precache
    if method == "cr":
        tasks.basic_multi_threaded(_retrieve_image, [((p,), None) for p in manga.pages])
        return ctx.reply(redirect(url_for("manga.reader_dispatch", manga=manga.id, method="r")))
    # Check if we need to fetch from source instead of proxies
    source = False
    if method in ("r-s", "ir-s"):
        source = True

    if page not in [p[0] for p in manga.pages]:
        mflash("<b>Not found.</b> Page not found.", "danger")
        return ctx.reply(redirect(url_for("manga.view", manga=manga.id)))

    meta = _gen_viewer_metadata(manga, method, page)
    if method in ("ir", "ir-s"):
        if source:
            images = [_retrieve_image(p, source) for p in manga.pages]
        else:
            results = {}
            tasks.basic_multi_threaded(_retrieve_image, [((p,), None) for p in manga.pages], results)
            images = [x[1] for x in sorted(results.items())]
        return ctx.reply(render_template("manga_reader_inf.html", ctx=ctx, m=manga, images=images, **meta))

    image = _retrieve_image(manga.pages[page - 1], source)
    return ctx.reply(render_template("manga_reader.html", ctx=ctx, m=manga, image=image, **meta))


def download_dispatch(ctx, manga, method, filetype):
    return ctx.reply("Not Implemented Yet")


def _retrieve_image(page, from_source=False, task_data=None):
    if from_source:
        return page[1]
    elif task_data is not None:  # "return" for threads
        task_data[page[0]] = get_url(page[2], page[1])
    else:
        return get_url(page[2], page[1])


def _gen_viewer_metadata(manga, method, page):
    return {
        "a_prev": f"/m/{manga.id}/{method}/{page - 1}" if page > 1 else "#",
        "a_next": f"/m/{manga.id}/{method}/{page + 1}" if page < len(manga.pages) else "#",
        "a_back": f"/m/{manga.id}",
        "pb_current": page,
        "pb_total": len(manga.pages),
        "pb_pct": round((page / len(manga.pages)) * 100),
        "s_text": _inv_str(method),
        "s_url": f"/m/{manga.id}/{_inv(method)}/{page}" if page > 1 else f"/m/{manga.id}/{_inv(method)}"
    }


def _inv(method):
    inverse = {
        "r": "r-s",
        "r-s": "r",
        "ir": "ir-s",
        "ir-s": "ir"
    }
    return inverse[method]


def _inv_str(method):
    inverse = {
        "r": "Source Reader",
        "r-s": "Proxied Reader",
        "ir": "Source InfiniteScroll™",
        "ir-s": "Proxied InfiniteScroll™"
    }
    return inverse[method]
