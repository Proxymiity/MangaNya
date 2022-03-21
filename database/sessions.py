from database.connector import db, dbc


def create(token, user, ip, ua, _type):
    dbc.execute("insert into sessions (token, user_id, ip, ua, type) "
                "values (%s, %s, %s, %s, %s) returning *",
                (token, user, ip, ua, _type))
    db.commit()
    w = dbc.fetchall()[0]
    print(f"I:[database/sessions] Created {w[0]}:{user}")
    return w


def delete(token):
    dbc.execute("delete from sessions where token = %s", (token,))
    db.commit()
    print(f"I:[database/sessions] Deleted {token}")


def extend(token, ip, ua):
    dbc.execute("update sessions set ip = %s, ua = %s, "
                "expires_at = now() + interval '1' month, last_activity = now() "
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
