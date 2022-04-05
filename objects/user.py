import bcrypt
from datetime import datetime

from database import users
from utils import validation, conf
import exceptions

SALT = conf.get("auth", "salt").encode("utf-8")
req_prop = ("username", "password", "email")


class User:
    def __init__(self, *args, **kwargs):
        self.id = int(0)
        self.username = str()
        self.password = str()
        self.email = str()
        self.private = bool(False)
        self.state = int(0)
        self.admin = bool(False)
        self.uploader = bool(False)
        self.created_at = datetime
        self.updated_at = datetime
        self.last_login = datetime
        if args:
            _items = [x[0] for x in list(self.__dict__.items())]
            for i in range(len(args)):
                self.__dict__[_items[i]] = args[i]
        if kwargs:
            self.__dict__.update(kwargs)

    def create(self):
        validation.validate_model(self, req_prop)
        if self.id != 0:
            raise exceptions.EntryExistsError
        x = users.create(self.username, self.password, self.email, self.private, self.state, self.admin, self.uploader)
        self.__init__(*x)

    def delete(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        users.delete(self.id)
        self.id = 0

    def update(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        users.update(self.id,
                     self.username, self.password, self.email, self.private, self.state, self.admin, self.uploader)

    def set_pw(self, password):
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), SALT)
        self.password = hashed_pw.decode("utf-8")

    def check_pw(self, password):
        hashed_pw = self.password.encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), hashed_pw)

    @classmethod
    def from_id(cls, id_):
        x = users.from_id(id_)
        return cls(*x) if x else None

    @classmethod
    def from_username(cls, username):
        x = users.from_username(username)
        return cls(*x) if x else None

    @classmethod
    def from_email(cls, email):
        x = users.from_email(email)
        return cls(*x) if x else None
