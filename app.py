from flask import Flask, render_template

from utils.auth import Context
from utils.web import mflash
from utils import conf

from views import account

app = Flask(__name__)
app.secret_key = conf.get("auth", "secret_key")
app.register_blueprint(account)


if conf.get("main", "env", "prod") == "prod":
    @app.errorhandler(Exception)
    def exception_handler(e):
        print(f"Error occurred: {e} {e.args}")
        try:
            ctx = Context()
            mflash("<b>Internal Server Error.</b> Could not process your request. Please try again later.", "danger")
            return ctx.reply(render_template("base.html", ctx=ctx))
        except Exception as exc:
            print(f"Error occurred trying to render error: {exc} {exc.args}")
            return "Internal Server Error", 500


# Temporary route to at least get the navbar
@app.route("/")
def index():
    ctx = Context()
    return ctx.reply(render_template("base.html", ctx=ctx))


if __name__ == '__main__':
    app.run(debug=True, ssl_context=("fullchain.pem", "privkey.pem"), port=443)  # Temporary env for testing
