from typing import Dict, List
import requests

import bs4

from content_providers import HackerNewsContentProvider, IndieHackerContentProvider

class InvalidRequestException(Exception):
    pass


content_providers = [HackerNewsContentProvider(), IndieHackerContentProvider()]
internet: Dict[str, List[Dict[str, object]]] = {}

for c in content_providers:
    resp = requests.get(c.getBaseWebsite())
    if resp.status_code != 200:
        raise InvalidRequestException("Invalid status code {} from website {}. {}".format(resp.url, c.getBaseWebsite, resp.reason))

    soup = bs4.BeautifulSoup(resp.content, "html.parser")
    internet[c.getContentId()] = c.getContent(soup)

print(internet)