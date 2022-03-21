from database.connector import db, dbc


def create(type_, uploader, title, language, cover, state=0):
    dbc.execute("insert into manga (state, type, uploader, title, language, cover) "
                "values (%s, %s, %s, %s, %s, %s) returning *",
                (state, type_, uploader, title, language, cover))
    db.commit()
    w = dbc.fetchall()[0]
    print(f"I:[database/manga] Created {w[0]}:{title}")
    return w


def delete(id_):
    dbc.execute("delete from manga where id = %s", (id_,))
    db.commit()
    print(f"I:[database/manga] Deleted {id_}")


def update(id_, state, type_, uploader, title, language):
    dbc.execute("update manga set state = %s, type = %s, uploader = %s, "
                "title = %s, language = %s, updated_at = now() "
                "where id = %s",
                (state, type_, uploader, title, language, id_))
    db.commit()
    print(f"I:[database/manga] Updated {id_}:{title}")


def from_id(id_, full=True):
    dbc.execute("select * from manga where id = %s", (id_,))
    try:
        m = dbc.fetchall()[0]
    except IndexError:
        return None
    if full:
        dbc.execute("select * from mg_meta_artists where id = %s", (id_,))
        mma = [x[1] for x in dbc.fetchall()]
        dbc.execute("select * from mg_meta_groups where id = %s", (id_,))
        mmg = [x[1] for x in dbc.fetchall()]
        dbc.execute("select * from mg_meta_sauces where id = %s", (id_,))
        mms = [x[1] for x in dbc.fetchall()]
        dbc.execute("select * from mg_meta_tags where id = %s", (id_,))
        mmt = [x[1] for x in dbc.fetchall()]
        dbc.execute("select * from mg_pages where id = %s", (id_,))
        mp = [(x[1], x[2], x[3]) for x in dbc.fetchall()]
        dbc.execute("select * from mg_associations where id = %s", (id_,))
        try:
            _ma = dbc.fetchall()[0]
            ma = (_ma[1], _ma[2], _ma[3])
        except IndexError:
            ma = (None, None, None)
        return m, mma, mmg, mms, mmt, mp, ma
    else:
        return m, None, None, None, None, None, None


def update_meta(id_, artists, groups, sauces, tags):
    dbc.execute("delete from mg_meta_artists where id = %s", (id_,))
    dbc.execute("delete from mg_meta_groups where id = %s", (id_,))
    dbc.execute("delete from mg_meta_sauces where id = %s", (id_,))
    dbc.execute("delete from mg_meta_tags where id = %s", (id_,))
    for x in artists:
        dbc.execute("insert into mg_meta_artists (id, name) values (%s, %s)", (id_, x))
    for x in groups:
        dbc.execute("insert into mg_meta_groups (id, name) values (%s, %s)", (id_, x))
    for x in sauces:
        dbc.execute("insert into mg_meta_sauces (id, name) values (%s, %s)", (id_, x))
    for x in tags:
        dbc.execute("insert into mg_meta_tags (id, name) values (%s, %s)", (id_, x))
    db.commit()
    print(f"I:[database/manga] Updated {id_} meta")


def update_pages(id_, pages):
    dbc.execute("delete from mg_pages where id = %s", (id_,))
    for x in pages:
        dbc.execute("insert into mg_pages (id, page, url, proxy) "
                    "values (%s, %s, %s, %s)",
                    (id_, x[0], x[1], x[2]))
    db.commit()
    print(f"I:[database/manga] Updated {id_} pages")


def update_association(id_, src_id, src_name, src_cd):
    dbc.execute("delete from mg_associations where id = %s", (id_,))
    dbc.execute("insert into mg_associations (id, source_id, source_name, source_date) "
                "values (%s, %s, %s, %s)",
                (id_, src_id, src_name, src_cd))
    db.commit()
    print(f"I:[database/manga] Updated {id_} association")


def remove_association(id_):
    dbc.execute("delete from mg_associations where id = %s", (id_,))
    db.commit()
    print(f"I:[database/manga] Removed {id_} association")
