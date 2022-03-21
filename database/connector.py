import psycopg2
from utils import conf
from pxyTools import dataIO
# Commented for compatibility with Windows envs during early development.
# from uwsgidecorators import postfork

cfg = conf.load("database")
db = None
dbc = None


def sanitize(val):
    return "".join(x for x in val if x.isalnum() or x == "_")


# Commented for compatibility with Windows envs during early development.
# @postfork
# def _uwsgi_post_fork():
#     connect()


def connect():
    global db
    global dbc
    if db is not None:
        print("I:[database/connector] Closing active database session")
        dbc.close()
        db.close()
    print("I:[database/connector] Connecting to database")
    db = psycopg2.connect(host=cfg["host"], port=cfg["port"],
                          user=cfg["username"], password=cfg["password"], dbname=cfg["database"])
    db.autocommit = False
    dbc = db.cursor()


if conf.get("main", "uwsgi") is False:
    connect()
