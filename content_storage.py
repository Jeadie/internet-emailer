from datetime import datetime, timedelta
from typing import Dict, List
import json 

import sqlite3
from peewee import AutoField, CharField, DateTimeField, ForeignKeyField, Model, SqliteDatabase, TextField

from content_providers import ContentId, InternetContent

DB= SqliteDatabase("the-internet.db")
class BaseModel(Model):
    class Meta:
        database = DB

class InternetLocation(BaseModel):
    location_type = CharField(unique=True)

class InternetContent(BaseModel):
    id = CharField(unique=True)
    timestamp = DateTimeField()
    title = CharField()
    url = CharField()

    location = ForeignKeyField(InternetLocation, backref="contents")

    # JSON encoded
    content: TextField()


class ContentStorage(object):

    def __init__(self) -> None:
        with DB:
            DB.create_tables([InternetContent, InternetLocation])

    def _get_or_create_internet_locations(self, content: List[InternetContent]) -> Dict[ContentId, InternetContent]:
        """ Maps the content types of InternetContentProvider to their InternetLocation. Does not
        recreate InternetLocation if they exist. 
        """
        content_types = list(map(lambda x: x.content_type, content))
        type_location_map = {}
        for t in content_types:
            l, _ = InternetLocation.get_or_create(location_type=t)
            type_location_map[t] = l
        return type_location_map

    def save(self, internet_content: List[InternetContent]):
        """ Saves a list of internet content.
        
        """
        content_type_to_internet_location = self._get_or_create_internet_locations(internet_content)

        # The bulk_create API doesn't set the fk value automatically.
        with DB.atomic():
            for c in internet_content:
                InternetContent.get_or_create(
                    id=c.id,
                    defaults = {
                        "timestamp" : c.timestamp,
                        "title" : c.title,
                        "url" : c.url,
                        "location" : content_type_to_internet_location[c.content_type],
                        "content" : json.dumps(c.content)    
                    }
                )

    def get(self, last_n_days=7) -> List[InternetContent]:
        return []