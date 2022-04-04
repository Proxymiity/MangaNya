import exceptions
from flask import request, make_response
from objects import User, Session
from json import dumps
from datetime import datetime
import re
SPACE = " "
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def _extract_token():
    cookie = request.cookies.get("auth_token")
    if cookie:
        return cookie.strip()
    header = request.headers.get("X-Auth-Token")
    if header:
        return header.strip()
    param = request.args.get("token")
    if param:
        return param.strip()
    return None


class Context:
    def __init__(self, extend=True):
        self.session = None
        self.user = None
        self.token = None
        tk = _extract_token()
        if tk:
            self.token = tk
            sess = Session.from_token(tk)
            if sess:
                if datetime.utcnow() >= sess.expires_at or 0:
                    sess = None
            if sess:
                user = User.from_id(sess.user)
                if user:
                    self.session = sess
                    self.user = user
                    if extend:
                        sess.extend(request.remote_addr, request.headers.get("User-Agent", "?"))

    def reply(self, response, status=200, set_cookies=True):
        r = make_response(response)
        r.status = status
        if set_cookies:
            if _extract_token() and not self.session:
                r.delete_cookie("auth_token", secure=True, samesite="strict")
            if not _extract_token() and self.session:
                r.set_cookie("auth_token", self.session.token, secure=True, samesite="strict")
        return r

    def reply_json(self, json, status=200, set_cookies=False):
        data = dumps(json, separators=None, indent=None, sort_keys=False)
        r = self.reply(data, status, set_cookies)
        r.headers["Content-Type"] = "application/json"
        return r


def _validate_username(username):
    if not 4 <= len(username) <= 32:
        raise exceptions.FieldValidationError
    if SPACE in username:
        raise exceptions.FieldValidationError
    if not all([x.isalnum() or x == '_' for x in username]):
        raise exceptions.FieldValidationError


def _validate_email(email):
    if not 5 <= len(email) <= 128:
        raise exceptions.FieldValidationError
    if SPACE in email:
        raise exceptions.FieldValidationError
    if not re.fullmatch(EMAIL_REGEX, email):
        raise exceptions.FieldValidationError


def _validate_password(password):
    if not 8 <= len(password) <= 64:
        raise exceptions.FieldValidationError
    if SPACE in password:
        raise exceptions.FieldValidationError
    try:
        password.encode("utf-8")
    except UnicodeError:
        raise exceptions.FieldValidationError


def login(ctx, username, password):
    _validate_username(username)
    _validate_password(password)
    user = User.from_username(username)
    if not user:
        raise exceptions.InvalidUsernameError
    if not user.check_pw(password):
        raise exceptions.InvalidPasswordError
    ctx.session = Session.create(user, request.remote_addr, request.headers.get("User-Agent", "?"))
    ctx.user = User.from_id(ctx.session.user)
    ctx.token = ctx.session.token


def logout(ctx):
    if ctx.session:
        ctx.session.delete()
    ctx.session = None
    ctx.user = None
    ctx.token = None


def register(ctx, username, email, password):
    _validate_username(username)
    _validate_email(email)
    _validate_password(password)
    ut1 = User.from_username(username)
    ut2 = User.from_email(email)
    if ut1:
        raise exceptions.UsernameUsedError
    if ut2:
        raise exceptions.EmailUsedError
    user = User()
    user.username = username
    user.email = email
    user.set_pw(password)
    user.create()
    ctx.session = Session.create(user, request.remote_addr, request.headers.get("User-Agent", "?"))
    ctx.user = User.from_id(ctx.session.user)
    ctx.token = ctx.session.token
