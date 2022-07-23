from flask import Blueprint, request, render_template, redirect, url_for
from datetime import datetime

from objects import Session
from exceptions import (FieldValidationError, UserStateError,
                        InvalidUsernameError, InvalidPasswordError,
                        UsernameUsedError, EmailUsedError)
from utils import auth
from utils.auth import Context
from utils.web import mflash, time_str, time_ago

bp = Blueprint("account", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    ctx = Context()
    if ctx.session:
        mflash("You're already logged in.", "warning")
        return ctx.reply(redirect(url_for("home.index")))
    if request.method == "GET":
        return ctx.reply(render_template("login.html", ctx=ctx))
    req_user = request.form.get("username")
    req_pass = request.form.get("password")
    if not all([req_user, req_pass]):
        mflash("<b>Missing required fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(render_template("login.html", ctx=ctx))
    try:
        auth.login(ctx, req_user.strip(), req_pass.strip())
        mflash("<b>Successfully logged in.</b> Welcome back!", "success")
        return ctx.reply(redirect(url_for("home.index")))
    except (FieldValidationError, InvalidUsernameError, InvalidPasswordError):
        mflash("<b>Invalid username or password.</b> Please check your credentials and try again.", "danger")
        return ctx.reply(render_template("login.html", ctx=ctx))
    except UserStateError as e:
        if e.user.state == auth.state_id("BANNED"):
            mflash("<b>Cannot log in.</b> You are banned from this website.", "danger")
        elif e.user.state == auth.state_id("WAITING_DELETION"):
            mflash("<b>Cannot log in.</b> Your account is awaiting deletion.", "danger")
        else:
            mflash("<b>Cannot log in.</b> Invalid user state.", "danger")
        return ctx.reply(render_template("login.html", ctx=ctx))


@bp.route("/logout", methods=["GET"])
def logout():
    ctx = Context(extend=False)
    auth.logout(ctx)
    mflash("<b>Successfully logged out.</b> See you later!", "success")
    return ctx.reply(redirect(url_for("home.index")))


@bp.route("/register", methods=["GET", "POST"])
def register():
    ctx = Context()
    if ctx.session:
        mflash("You're already logged in.", "warning")
        return ctx.reply(redirect(url_for("home.index")))

    if request.method == "GET":
        return ctx.reply(render_template("register.html", ctx=ctx))

    req_user = request.form.get("username")
    req_email = request.form.get("email")
    req_pass = request.form.get("password")

    # Validate fields before registering the user
    if not all([req_user, req_email, req_pass]):
        mflash("<b>Missing required fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(render_template("register.html", ctx=ctx))

    try:
        auth.register(ctx, req_user.strip(), req_email.strip(), req_pass.strip())
        mflash("<b>Successfully registered.</b> Welcome to MangaNya!", "success")
        return ctx.reply(redirect(url_for("home.index")))
    except FieldValidationError:
        mflash("<b>Error validating fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(render_template("register.html", ctx=ctx), status=400)
    except UsernameUsedError:
        mflash("<b>Username already in use.</b> Please choose another username.", "danger")
        return ctx.reply(render_template("register.html", ctx=ctx), status=400)
    except EmailUsedError:
        mflash("<b>Email already in use.</b> Please choose another email address.", "danger")
        return ctx.reply(render_template("register.html", ctx=ctx), status=400)


@bp.route("/account", methods=["GET", "POST"])
def account():
    ctx = Context()
    if not ctx.session:
        mflash("You need to be logged in to access this page.", "warning")
        return ctx.reply(redirect(url_for("account.login")))

    if request.method == "GET":
        if ctx.user.state == auth.state_id("RESTRICTED"):
            mflash("<b>Account restricted.</b> Your account has been limited to a read-only state.", "warning")

        # Get all sessions, sort them by token so the user roughly gets the same order and put details in a list
        sessions = Session.from_user(ctx.user)
        sessions.sort(key=lambda x: x.token)
        devices = [(i+1, sessions[i].type or "-",
                    sessions[i].ip, sessions[i].ua, time_str(sessions[i].started_at),
                    time_ago(sessions[i].last_activity)) for i in range(len(sessions))]
        # An ugly way to get user's permissions. Since there is not too many, it's fine to do it this way
        perms = []
        perms.append("Administrator") if ctx.user.admin else None
        perms.append("Uploader") if ctx.user.uploader else None
        # Format dates to strings
        history = {
            "created_at": time_str(ctx.user.created_at),
            "updated_at": time_str(ctx.user.updated_at),
            "last_login": time_str(ctx.user.last_login)
        }
        return ctx.reply(render_template("account.html", ctx=ctx, perms=perms, history=history, devices=devices,
                                         state=auth.state_name(ctx.user.state).capitalize(),
                                         visibility="Private" if ctx.user.private else "Public"))

    if ctx.user.state == auth.state_id("RESTRICTED"):
        mflash("<b>Account restricted.</b> Cannot edit account details.", "danger")
        return ctx.reply(redirect(url_for("account.account")))

    req_user = request.form.get("username", "")
    req_email = request.form.get("email", "")
    req_pass = request.form.get("password", "")
    req_act_pass = request.form.get("actual_password", "")

    # Check that request has old password and at least one field set
    if not req_act_pass and not any([req_user, req_email, req_pass]):
        mflash("<b>Error validating fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
    # Check that the user's current password is correct
    if not ctx.user.check_pw(req_act_pass.strip()):
        mflash("<b>Invalid password.</b> Please check your credentials and try again.", "danger")
        return ctx.reply(redirect(url_for("account.account")))

    # Actually edit the user - redirects are here to force browsers to reload the page and discard post data
    try:
        auth.edit_user(ctx, req_user.strip(), req_email.strip(), req_pass.strip())
    except FieldValidationError:
        mflash("<b>Error validating fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
    except UsernameUsedError:
        mflash("<b>Username already in use.</b> Please choose another username.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
    except EmailUsedError:
        mflash("<b>Email already in use.</b> Please choose another email address.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
    mflash("<b>Successfully edited account.</b> Please ensure that you login with your new credentials next time.",
           "success")
    return ctx.reply(redirect(url_for("account.account")))


@bp.route("/account/profile_visibility", methods=["POST"])
def profile_visibility():
    ctx = Context()
    if not ctx.session or ctx.user.state == auth.state_id("RESTRICTED"):
        return _edit_account_deny(ctx)

    # Check if mode is valid
    mode = request.form.get("mode", "")
    if not mode or mode.strip() not in ("public", "private"):
        mflash("<b>Error validating fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(redirect(url_for("account.account")))

    # Change visibility and reply accordingly
    if mode.strip() == "private":
        ctx.user.private = True
        mflash("<b>Successfully change profile visibility.</b> Your profile is now private.", "success")
    else:
        ctx.user.private = False
        mflash("<b>Successfully change profile visibility.</b> Your profile is now public.", "success")
    ctx.user.update()

    return ctx.reply(redirect(url_for("account.account")))


@bp.route("/account/api_key", methods=["POST"])
def api_key():
    ctx = Context()
    if not ctx.session or ctx.user.state == auth.state_id("RESTRICTED"):
        return _edit_account_deny(ctx)

    # Check if key type is valid and user has permissions to create a key
    key_type = request.form.get("type", "")
    if not key_type or key_type.strip() not in ("trackable", "permanent"):
        mflash("<b>Error validating fields.</b> Please check that you correctly filled the form.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
    if key_type.strip() == "permanent" and not ctx.user.uploader:
        mflash("<b>Not enough permissions.</b> A permanent key requires the uploader permission.", "danger")
        return ctx.reply(redirect(url_for("account.account")))

    # Create session
    if key_type.strip() == "permanent":
        new_session = Session.create(ctx.user, "0.0.0.0", "Permanent API Key (non trackable)")
        new_session.expires_at = datetime.strptime("2032-01-01", "%Y-%m-%d")
        new_session.update()
    else:
        new_session = Session.create(ctx.user, "0.0.0.0", "Trackable API Key (never used)")

    mflash("<b>Successfully created API Key.</b> Please write down this code, you'll never see it again: "
           f"<code>{new_session.token}</code>", "success")
    return ctx.reply(redirect(url_for("account.account")))


@bp.route("/account/clear_sessions", methods=["POST"])
def clear_sessions():
    ctx = Context(extend=False)
    if not ctx.session or ctx.user.state == auth.state_id("RESTRICTED"):
        return _edit_account_deny(ctx)

    # Kill all sessions and log out the user
    [s.delete() for s in Session.from_user(ctx.user)]
    auth.logout(ctx)

    mflash("<b>Successfully logged out all devices.</b> Please note that any API key you may have created have "
           "been revoked.", "success")
    return ctx.reply(redirect(url_for("home.index")))


@bp.route("/account/delete_account", methods=["POST"])
def delete_account():
    ctx = Context(extend=False)
    if not ctx.session or ctx.user.state == auth.state_id("RESTRICTED"):
        return _edit_account_deny(ctx)

    # Check the user's password
    password = request.form.get("password", "")
    if not password or not ctx.user.check_pw(password.strip()):
        mflash("<b>Invalid password.</b> Please check your credentials and try again.", "danger")
        return ctx.reply(redirect(url_for("account.account")))

    # Set the user state to 'waiting for deletion'
    ctx.user.state = 3
    ctx.user.update()
    # Kill all sessions and log out the user
    [s.delete() for s in Session.from_user(ctx.user)]
    auth.logout(ctx)

    mflash("<b>Successfully deleted account.</b> Please note that for security reasons, you won't be able to "
           "create a new account with the same username or email for a couple hours.", "success")
    return ctx.reply(redirect(url_for("home.index")))


def _edit_account_deny(ctx):
    # Check if the user isn't logged in
    if not ctx.session:
        mflash("You need to be logged in to access this page.", "warning")
        return ctx.reply(redirect(url_for("account.login")))

    # Check if the user has a restricted state
    if ctx.user.state == auth.state_id("RESTRICTED"):
        mflash("<b>Account restricted.</b> Cannot edit account details.", "danger")
        return ctx.reply(redirect(url_for("account.account")))
