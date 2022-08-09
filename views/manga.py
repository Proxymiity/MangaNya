from flask import Blueprint, render_template, url_for, redirect, send_file
from math import ceil
from time import sleep

import requests
from urllib.parse import urlparse

from pathlib import Path
from shutil import rmtree

from objects import Manga, MangaType, User
from objects.manga import state_name
from utils.auth import Context
from utils.web import gen_paginate_data, mflash, fmt_int
from utils.proxy import get_url
from utils import tasks
from utils.files import make_pdf, make_zip

from exceptions import TransformationError

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
    source = False
    if method == "dl-s":
        source = True
    if filetype not in ("pdf", "zip"):
        mflash("<b>Unknown method.</b> Viewing method wasn't found.", "danger")
        return ctx.reply(redirect(url_for("manga.view", manga=manga.id)))

    # Create a task ID to bundle with metadata
    i = str(tasks.uuid4())
    d = tasks.create_task_meta("manga.download_task", {"task": i}, kind="manga_download",
                               info="Downloading Manga...")
    # Start task and wait client-side
    t = tasks.task_single_threaded(_download_target, [((manga, source, filetype), None)],
                                   data=d, task_id=i, keep=False)
    return ctx.reply(tasks.client_side_wait(t))


@bp.route("/manga/download/<string:task>")
def download_task(task):
    ctx = Context()
    task_data = tasks.get_task(task)
    if not task_data[0]:  # No task found with that ID
        mflash("<b>Task not found.</b> No tasks were found with this ID.", "danger")
        return ctx.reply(redirect(url_for("home.index")))
    if task_data[1]["_kind"] != "manga_download":  # Task isn't a manga download
        mflash("<b>Invalid task.</b> This task does not result in a manga download.", "danger")
        return ctx.reply(redirect(url_for("home.index")))

    # We're sure this is a manga download, check if it succeeded
    manga_id = task_data[1]["manga"]
    print(task_data)
    if task_data[1]["success"] is False:
        # At this point, either the download failed and there is a valid task_data failure,
        # or the user tried to access the task before it finished downloading.
        mflash(f"<b>Download failed.</b> {task_data[1].get('failure', 'Unknown error.')}", "danger")
        return ctx.reply(redirect(url_for("manga.view", manga=manga_id)))

    # The task succeeded, prepare download URL
    url = url_for("manga.download_task_file", task=task)
    meta = f'<meta http-equiv="refresh" content="3;url={url}" />'
    mflash(f"<b>Your task has finished processing.</b> Your download will start shortly.<br>"
           f"Not downloading? <a href=\"{url}\">Click here to start your download manually</a>.<br>"
           f"This link will expire in 2 minutes. {meta}", "success")
    return ctx.reply(redirect(url_for("manga.view", manga=manga_id)))


@bp.route("/manga/download/<string:task>/file")
def download_task_file(task):
    ctx = Context()
    task_data = tasks.get_task(task)
    if not task_data[0] or not task_data[1].get("_kind") or not task_data[1].get("success"):
        mflash("<b>Task not found.</b> It probably expired, did not succeed, or did not even exist.", "danger")
        return ctx.reply(redirect(url_for("home.index")))
    return ctx.reply(send_file(task_data[1]["path"], as_attachment=True,
                               download_name=task_data[1]["path"].split("/")[-1]))


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


def _download_target(manga, source, filetype, task_data):
    task_data["success"] = False
    task_data["manga"] = manga.id

    def _return_and_delete():
        # Ensure that we get the user out of the loop with enough time to download/take action
        task_data.save()
        tasks.set_task(task_data["_id"], True)
        sleep(120)
        # Then delete task data
        task_path = Path(f"tmp/{task_data.path.stem}")
        if task_path.exists():
            rmtree(task_path, ignore_errors=True)
        # Finally, return since task data won't be kept
        return

    # Get final image links from proxies or the source itself
    tasks.update_task_meta(task_data, progress="[1/3] Retrieving images links")
    if source:
        images = [_retrieve_image(p, source) for p in manga.pages]
    else:
        results = {}
        tasks.basic_multi_threaded(_retrieve_image, [((p,), None) for p in manga.pages], results)
        images = [x[1] for x in sorted(results.items())]

    # Download all images to a temporary folder (defined by the task id itself)
    Path(f"tmp/{task_data.path.stem}").mkdir(exist_ok=True)
    local_images = []
    for i, img in enumerate(images):
        tasks.update_task_meta(task_data, progress=f"[2/3] Downloading image {i+1}/{len(images)}")
        # Get a file name with leading zeroes to keep order in file explorers
        name = fmt_int(i+1, len(str(len(images))))
        # Extension is parsed from the end of the URL
        # This may not be a reliable way (e.g. site.com/content.php?page=4), may need a header-based setting later on
        ext = str(urlparse(img).path).split("/")[-1].split(".")[-1]
        with requests.get(img) as r:
            # Can always be fined tuned with a r.status_code in (200, ...) or str(r.status_code).startswith()
            if r.ok:
                p = Path(f"tmp/{task_data.path.stem}/{name}.{ext}")
                p.write_bytes(r.content)
                local_images.append(p)
            else:
                task_data["failure"] = f"Could not download image {i+1}"
                _return_and_delete()

    if filetype == "pdf":
        tasks.update_task_meta(task_data, progress=f"[3/3] Rendering PDF")
        dest = Path(f"tmp/{task_data.path.stem}/MangaNya-{manga.id}.manga.pdf")
        try:
            make_pdf(local_images, dest)
        except TransformationError:
            task_data["failure"] = f"Could not transform images."
            _return_and_delete()
        task_data["path"] = str(dest)
        task_data["success"] = True
    elif filetype == "zip":
        tasks.update_task_meta(task_data, progress=f"[3/3] Making archive")
        dest = Path(f"tmp/{task_data.path.stem}/MangaNya-{manga.id}.manga.zip")
        make_zip(local_images, dest)
        task_data["path"] = str(dest)
        task_data["success"] = True
    else:
        task_data["failure"] = f"Unmatched filetype (shouldn't be possible?)"
    _return_and_delete()
