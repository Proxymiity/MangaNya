from pxyTools import dataIO
cache = {}


def get(f, k, dv=None):
    global cache
    f = _fn(f)
    if f not in cache:
        cache[f] = dataIO.load_json(f)
    return cache[f].get(k, dv)


def put(f, k, v):
    global cache
    f = _fn(f)
    if f not in cache:
        cache[f] = dataIO.load_json(f)
    cache[f][k] = v
    save(f)


def load(f):
    global cache
    f = _fn(f)
    if f not in cache:
        cache[f] = dataIO.load_json(f)
    return cache[f]


def save(f, d=None):
    global cache
    f = _fn(f)
    if d:
        cache[f] = d
    dataIO.save_json(f, cache[f])


def drop_caches():
    global cache
    cache = {}


def _fn(f):
    return f"config/{f}.json"
