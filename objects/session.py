import exceptions
from database import sessions
from datetime import datetime
from utils import validation
from secrets import token_urlsafe
req_prop = ("token", "user", "ip", "ua")


class Session:
    def __init__(self, *args, **kwargs):
        self.token = str()
        self.user = int()
        self.ip = str()
        self.ua = str()
        self.type = str()
        self.started_at = datetime
        self.expires_at = datetime
        self.last_activity = datetime
        if args:
            _items = [x[0] for x in list(self.__dict__.items())]
            for i in range(len(args)):
                self.__dict__[_items[i]] = args[i]
        if kwargs:
            self.__dict__.update(kwargs)

    @classmethod
    def create(cls, user, ip, ua, _type=None):
        tk = token_urlsafe(32)
        x = sessions.create(tk, user.id, ip, ua, _type)
        return cls(*x)

    def delete(self):
        validation.validate_model(self, req_prop)
        if not self.token:
            raise exceptions.EntryNotFoundError
        sessions.delete(self.token)
        self.token = str()

    def extend(self, ip=None, ua=None):
        validation.validate_model(self, req_prop)
        if not self.token:
            raise exceptions.EntryNotFoundError
        sessions.extend(self.token, ip if ip else self.ip, ua if ua else self.ua)

    @classmethod
    def from_token(cls, token):
        x = sessions.from_token(token)
        return cls(*x) if x else None

    @classmethod
    def from_user(cls, user):
        x = sessions.from_user(user.id)
        return [cls(*y) for y in x]
