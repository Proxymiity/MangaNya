from database.connector import db, dbc


def create(token, user, ip, ua, type_):
    dbc.execute("update users set last_login = (now() at time zone 'utc') "
                "where id = %s", (user,))
    dbc.execute("insert into sessions (token, user_id, ip, ua, type) "
                "values (%s, %s, %s, %s, %s) returning *",
                (token, user, ip, ua, type_))
    db.commit()
    w = dbc.fetchall()[0]
    print(f"I:[database/sessions] Created {w[0]}:{user}")
    return w


def delete(token):
    dbc.execute("delete from sessions where token = %s", (token,))
    db.commit()
    print(f"I:[database/sessions] Deleted {token}")


def update(token, user, ip, ua, type_, started_at, expires_at, last_activity):
    dbc.execute("update sessions set user_id = %s, ip = %s, ua = %s, type = %s, "
                "started_at = %s, expires_at = %s, last_activity = %s "
                "where token = %s",
                (user, ip, ua, type_, started_at, expires_at, last_activity, token))
    db.commit()
    print(f"I:[database/sessions] Updated {token}")


def extend(token, ip, ua):
    dbc.execute("update sessions set ip = %s, ua = %s, "
                "expires_at = (now() at time zone 'utc') + interval '1' month, "
                "last_activity = (now() at time zone 'utc') "
                "where token = %s ",
                (ip, ua, token))
    db.commit()
    print(f"I:[database/sessions] Extended {token}")


def from_token(token):
    dbc.execute("select * from sessions where token = %s", (token,))
    try:
        return dbc.fetchall()[0]
    except IndexError:
        return None


def from_user(id_):
    dbc.execute("select * from sessions where user_id = %s", (id_,))
    try:
        return dbc.fetchall()
    except IndexError:
        return None
