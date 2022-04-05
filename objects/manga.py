from datetime import datetime

from database import manga
from utils import validation
import exceptions

req_prop = ("type", "uploader", "title", "language", "cover")


class Manga:
    def __init__(self, *args, **kwargs):
        self.id = int(0)
        self.state = int(0)
        self.type = str()
        self.uploader = int()
        self.title = str()
        self.language = str()
        self.cover = str()
        self.created_at = datetime
        self.updated_at = datetime
        # mg_meta_*
        self.artists = []
        self.groups = []
        self.sauces = []
        self.tags = []
        # mg_pages
        self.pages = []
        # mg_associations
        self.source_id = None
        self.source_name = None
        self.source_created_at = None
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
        x = manga.create(self.type, self.uploader, self.title, self.language, self.cover, self.state)
        self.__init__(*x)

    def delete(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        manga.delete(self.id)
        self.id = 0

    def update(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        manga.update(self.id,
                     self.state, self.type, self.uploader, self.title, self.language)

    def update_meta(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        manga.update_meta(self.id,
                          self.artists, self.groups, self.sauces, self.tags)
        self.update()

    def update_pages(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        manga.update_pages(self.id, self.pages)
        self.update()

    def update_association(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        if self.source_id is None or self.source_name is None or self.source_created_at is None:
            return self.remove_association()
        manga.update_association(self.id,
                                 self.source_id, self.source_name, self.source_created_at)
        self.update()

    def remove_association(self):
        validation.validate_model(self, req_prop)
        if self.id == 0:
            raise exceptions.EntryNotFoundError
        manga.remove_association(self.id)
        self.source_id = self.source_name = self.source_created_at = None
        self.update()

    @classmethod
    def from_id(cls, id_, full=True):
        x = manga.from_id(id_, full)
        if x:
            z = x[0] + (x[1], x[2], x[3], x[4], x[5]) + x[6]
            return cls(*z)
        return None
