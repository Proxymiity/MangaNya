import threading
from uuid import uuid4

from flask import url_for, redirect

from pxyTools import JSONDict
from pathlib import Path

jobs = JSONDict("tmp/jobs.json")


def basic_single_threaded(func, args, task_data=None):
    threads = []
    for a, k in args:
        k = k or {}
        if task_data is not None:
            k["task_data"] = task_data
        threads.append(threading.Thread(target=func, args=a, kwargs=k))
    for t in threads:
        t.start()
        t.join()


def basic_multi_threaded(func, args, task_data=None):
    threads = []
    for a, k in args:
        k = k or {}
        if task_data is not None:
            k["task_data"] = task_data
        threads.append(threading.Thread(target=func, args=a, kwargs=k))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def task_single_threaded(func, args, data=None, task_id=None, keep=True):
    task_id = task_id or str(uuid4())
    t = threading.Thread(target=_task_watcher, args=(task_id, data, basic_single_threaded, func, args, keep))
    t.start()
    return task_id


def task_multi_threaded(func, args, data=None, task_id=None, keep=True):
    task_id = task_id or str(uuid4())
    t = threading.Thread(target=_task_watcher, args=(task_id, data, basic_multi_threaded, func, args, keep))
    t.start()
    return task_id


def _task_watcher(task, tdata, tfunc, func, args, keep):
    task_data = JSONDict(f"tmp/{task}.job.json", data=tdata)
    task_data["_id"] = task
    set_task(task, False)
    task_data.save()
    tfunc(func, args, task_data)
    if keep:
        task_data.save()
        set_task(task, True)
    else:
        set_task(task, None)


def get_task(task):
    jobs.reload()
    state = jobs.get(task)
    data = JSONDict(f"tmp/{task}.job.json")
    return state, data


def set_task(task, state):
    jobs.reload()
    if state is None:
        jobs.pop(task)
        Path(f"tmp/{task}.job.json").unlink(missing_ok=True)
    else:
        jobs[task] = state
    jobs.save()


def create_task_meta(endpoint=None, endpoint_kwargs=None, data=None, kind=None, progress=None, info=None):
    if data is None:
        data = {}
    data["_endpoint"] = endpoint
    data["_endpoint_kwargs"] = endpoint_kwargs or {}
    data["_kind"] = kind
    data["_progress"] = progress or "No progress info available"
    data["_info"] = info
    return data


def update_task_meta(task_data, endpoint=None, endpoint_kwargs=None, kind=None, progress=None, info=None):
    task_data["_endpoint"] = endpoint or task_data["_endpoint"]
    task_data["_endpoint_kwargs"] = endpoint_kwargs or task_data["_endpoint_kwargs"]
    task_data["_kind"] = kind or task_data["_kind"]
    task_data["_progress"] = progress or task_data["_progress"]
    task_data["_info"] = info or task_data["_info"]
    task_data.save()


def client_side_wait(task):
    return redirect(url_for("tasks.wait", task=task))