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

class Content(BaseModel):
    id = CharField(unique=True)
    timestamp = DateTimeField()
    title = CharField()
    url = CharField()

    location = ForeignKeyField(InternetLocation, backref="contents")

    # JSON encoded
    additional_fields = TextField()


class ContentStorage(object):

    def __init__(self) -> None:
        with DB:
            DB.create_tables([Content, InternetLocation])

    def _get_or_create_internet_locations(self, content: List[InternetContent]) -> Dict[ContentId, InternetLocation]:
        """ Maps the content types of InternetContentProvider to their InternetLocation. Does not
        recreate InternetLocation if they exist. 
        """
        content_types = list(map(lambda x: x.content_type, content))
        type_location_map = {}
        for t in content_types:
            l, _ = InternetLocation.get_or_create(location_type=str(t))
            type_location_map[t] = l
        return type_location_map

    def save(self, internet_content: List[InternetContent]):
        """ Saves a list of internet content.
        
        """
        content_type_to_internet_location = self._get_or_create_internet_locations(internet_content)

        # The bulk_create API doesn't set the fk value automatically.
        with DB.atomic():
            for c in internet_content:
                Content.get_or_create(
                    id=c.id,
                    defaults = {
                        "timestamp" : c.timestamp,
                        "title" : c.title,
                        "url" : c.url,
                        "location" : content_type_to_internet_location[c.content_type],
                        "additional_fields" : json.dumps(c.content)    
                    }
                )

    def getLocation(self, content_id: ContentId) -> InternetLocation:
        return InternetLocation.get(
            InternetLocation.location_type == str(content_id)
        )

    def getLocations(self, content_ids: List[ContentId]) -> List[InternetLocation]:
        return [self.getLocation(c) for c in content_ids]

    def get(self, content_ids: List[ContentId] = ContentId.all(), last_n_days=7) -> List[InternetContent]:
        locations = self.getLocations(content_ids)
        location_id_to_content_id = dict([(l, l.location_type) for l in locations])

        q = (Content.select().where(
                (Content.location.in_(locations))  # & 
                # (Content.timestamp.to_timestamp() > (datetime.now() - timedelta(days=last_n_days)))
            )
        )
        return [self.toInternetContent(content, location_id_to_content_id) for content in q]

    def toInternetContent(self, c: Content, location_id_to_content_id: Dict[InternetLocation, str]) -> InternetContent:
        return InternetContent(
            c.id,
            c.timestamp,
            c.title,
            c.url,
            location_id_to_content_id[c.location],
            json.loads(c.additional_fields)
        )
