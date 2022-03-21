from database.connector import db, dbc


def create(username, password, email, state=0, admin=False, uploader=False):
    dbc.execute("insert into users (username, password, email, state, admin, uploader) "
                "values (%s, %s, %s, %s, %s, %s) returning *",
                (username, password, email, state, admin, uploader))
    db.commit()
    w = dbc.fetchall()[0]
    print(f"I:[database/users] Created {w[0]}:{username}")
    return w


def delete(id_):
    dbc.execute("delete from users where id = %s", (id_,))
    db.commit()
    print(f"I:[database/users] Deleted {id_}")


def update(id_, username, password, email, state, admin, uploader):
    dbc.execute("update users set username = %s, password = %s, email = %s, state = %s, "
                "admin = %s, uploader = %s, updated_at = now() "
                "where id = %s",
                (username, password, email, state, admin, uploader, id_))
    db.commit()
    print(f"I:[database/users] Updated {id_}:{username}")


def from_id(id_):
    dbc.execute("select * from users where id = %s", (id_,))
    try:
        return dbc.fetchall()[0]
    except IndexError:
        return None


def from_username(username):
    dbc.execute("select * from users where username = %s", (username,))
    try:
        return dbc.fetchall()[0]
    except IndexError:
        return None


def from_email(email):
    dbc.execute("select * from users where email = %s", (email,))
    try:
        return dbc.fetchall()[0]
    except IndexError:
        return None
