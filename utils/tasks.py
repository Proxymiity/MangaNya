import threading
from uuid import uuid4

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
        print(k)
        threads.append(threading.Thread(target=func, args=a, kwargs=k))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def task_single_threaded(func, args, data=None, task_id=None):
    task_id = task_id or str(uuid4())
    t = threading.Thread(target=_task_watcher, args=(task_id, data, basic_single_threaded, func, args))
    t.start()
    return task_id


def task_multi_threaded(func, args, data=None, task_id=None):
    task_id = task_id or str(uuid4())
    t = threading.Thread(target=_task_watcher, args=(task_id, data, basic_multi_threaded, func, args))
    t.start()
    return task_id


def _task_watcher(task, tdata, tfunc, func, args):
    task_data = JSONDict(f"tmp/{task}.job.json", data=tdata)
    set_task(task, False)
    tfunc(func, args, task_data)
    task_data.save()
    set_task(task, True)


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
