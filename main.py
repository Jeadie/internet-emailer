from typing import Dict, List
import requests

import bs4

from content_providers import HackerNewsContentProvider, IndieHackerContentProvider, InternetContent
from content_storage import ContentStorage, ContentId

class InvalidRequestException(Exception):
    pass


content_providers = [HackerNewsContentProvider(), IndieHackerContentProvider()]
storage = ContentStorage()

for c in content_providers:
    resp = requests.get(c.getBaseWebsite())
    if resp.status_code != 200:
        raise InvalidRequestException("Invalid status code {} from website {}. {}".format(resp.url, c.getBaseWebsite, resp.reason))

    soup = bs4.BeautifulSoup(resp.content, "html.parser")
    storage.save(c.getContent(soup))


for c in storage.get(content_ids=[ContentId.HackerNews_News], last_n_days=7):
    print(c)