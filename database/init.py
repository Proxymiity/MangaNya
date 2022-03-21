from database.connector import db, dbc
from objects import User, Manga
from datetime import datetime


def init():
    dbc.execute("drop table if exists user_mg_favorites;")
    dbc.execute("drop table if exists mg_meta_artists;")
    dbc.execute("drop table if exists mg_meta_groups;")
    dbc.execute("drop table if exists mg_meta_tags;")
    dbc.execute("drop table if exists mg_meta_sauces;")
    dbc.execute("drop table if exists mg_associations;")
    dbc.execute("drop table if exists mg_pages;")
    dbc.execute("drop table if exists manga;")
    dbc.execute("drop table if exists sessions;")
    dbc.execute("drop table if exists users;")

    dbc.execute(("create table users "
                 "( "
                 "id serial, "
                 "username text not null, "
                 "password text not null, "
                 "email text not null, "
                 "state int default 0 not null, "
                 "admin bool default false not null, "
                 "uploader bool default false not null, "
                 "created_at timestamp default now() not null, "
                 "updated_at timestamp default now() not null, "
                 "last_login timestamp default now() not null, "
                 "constraint users_pk "
                 "primary key (id) "
                 "); "))

    dbc.execute(("create unique index users_username_uindex "
                 "on users (username); "))

    dbc.execute(("create unique index users_email_uindex "
                 "on users (email); "))

    dbc.execute(("create table sessions"
                 "( "
                 "token text not null "
                 "constraint sessions_pk "
                 "primary key, "
                 "user_id int "
                 "constraint sessions_users_id_fk "
                 "references users "
                 "on update cascade on delete cascade, "
                 "ip text not null, "
                 "ua text not null, "
                 "type text, "
                 "started_at timestamp default now() not null, "
                 "expires_at timestamp default now() + interval '1' month not null, "
                 "last_activity timestamp default now() not null "
                 "); "))

    dbc.execute(("create table manga "
                 "( "
                 "id serial "
                 "constraint manga_pk "
                 "primary key, "
                 "state int default 0 not null, "
                 "type text not null, "
                 "uploader int not null "
                 "constraint manga_users_id_fk "
                 "references users (id), "
                 "title text, "
                 "language text not null, "
                 "cover text not null, "
                 "created_at timestamp default now() not null, "
                 "updated_at timestamp default now() not null "
                 "); "))

    dbc.execute(("create table mg_meta_artists "
                 "( "
                 "id int not null "
                 "constraint mg_meta_artists_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "name text not null, "
                 "constraint mg_meta_artists_pk "
                 "primary key (id, name) "
                 "); "))

    dbc.execute(("create table mg_meta_groups "
                 "( "
                 "id int not null "
                 "constraint mg_meta_groups_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "name text not null, "
                 "constraint mg_meta_groups_pk "
                 "primary key (id, name) "
                 "); "))

    dbc.execute(("create table mg_meta_tags "
                 "( "
                 "id int not null "
                 "constraint mg_meta_tags_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "name text not null, "
                 "constraint mg_meta_tags_pk "
                 "primary key (id, name) "
                 "); "))

    dbc.execute(("create table mg_meta_sauces "
                 "( "
                 "id int not null "
                 "constraint mg_meta_sauces_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "name text not null, "
                 "constraint mg_meta_sauces_pk "
                 "primary key (id, name) "
                 "); "))

    dbc.execute(("create table mg_associations "
                 "( "
                 "id int not null "
                 "constraint mg_associations_pk "
                 "primary key "
                 "constraint mg_associations_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "source_id text not null, "
                 "source_name text not null, "
                 "source_date date "
                 "); "))

    dbc.execute(("create unique index mg_associations_source_uindex "
                 "on mg_associations (source_id, source_name); "))

    dbc.execute(("create table mg_pages "
                 "( "
                 "id int not null "
                 "constraint mg_pages_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "page int not null, "
                 "url text not null, "
                 "proxy int default 0 not null, "
                 "constraint mg_pages_pk "
                 "primary key (id, page) "
                 "); "))

    dbc.execute(("create table user_mg_favorites "
                 "( "
                 "user_id int not null "
                 "constraint user_mg_favorites_users_id_fk "
                 "references users (id) "
                 "on update cascade on delete cascade, "
                 "id int not null "
                 "constraint user_mg_favorites_manga_id_fk "
                 "references manga (id) "
                 "on update cascade on delete cascade, "
                 "constraint user_mg_favorites_pk "
                 "primary key (user_id, id) "
                 "); "))
    db.commit()
    print("I:[database/init] Successfully(?) initialized tables and indexes")


def dummy():
    u = User()
    u.username = "test_user"
    u.set_pw("testPasswordForTestUser")
    u.email = "test@nya.network"
    u.admin = True
    u.create()
    m = Manga()
    m.type = "mango"
    m.uploader = u.id
    m.title = "Tales of Mango"
    m.language = "en"
    m.cover = "https://web-static.nya.network/md/no_cover.jpg"
    m.create()
    m.artists = ["SomeArtist", "SomeArtist2"]
    m.groups = ["YoloGroup1"]
    m.sauces = ["A ku na i tsu", "LMAO"]
    m.tags = ["hen tie"]
    m.update_meta()
    m.pages.append((0, 'url', 0))
    m.pages.append((1, 'url', 0))
    m.pages.append((2, 'url', 0))
    m.pages.append((3, 'url', 0))
    m.update_pages()
    m.source_id = "177013"
    m.source_name = "nHenThai"
    m.source_created_at = datetime.utcnow()
    m.update_association()
