from doctest import UnexpectedException
import bs4
from typing import Dict, List
import requests

class InternetContentProvider(object):
    """ Provides a uniform interface for internet content to be collected from different locations."""

    def getBaseWebsite(self) -> str:
        """ Returns the website to GET that contains the internet content."""
        pass

    def getContentId(self) -> str:
        """Returns the id for the content provider. Should not depend on the underlying content
        (i.e may relate to the sub-characteristics of a website, but not the specific content.
        """
        pass

    def getContent(self, page: bs4.BeautifulSoup) -> List[Dict[str, object]]:
        """Parses the internet content from a website, as a BeautifulSoup object, and returns a list
        of individual content payloads. An individiual payload represents a single consumable piece
        of content. 
        """
        pass


class IndieHackerContentProvider(InternetContentProvider):

    def getBaseWebsite(self) -> str:
        return "https://www.indiehackers.com"

    def getContentId(self) -> str:
        return "IndieHacker-post-popular"

    def getContent(self, page: bs4.BeautifulSoup) -> List[Dict[str, object]]:
        contentList = page.find(
            "div", class_="posts-section__posts"
            )
        items = contentList.find_all(
                class_="feed-item--post"
            )
        return list(map(lambda x: self.convertItemPost(x), items))

    def convertItemPost(self, x: bs4.Tag) -> Dict[str, object]:
        title_link = x.find("a", class_="feed-item__title-link")
        upvote_span = x.find("span", class_="feed-item__likes-count")
        comment_span = x.find("span", class_="reply-count__full-count")

        return {
            "title": title_link.get_text().strip(),
            "full_link": self.getBaseWebsite() + title_link.get('href'),
            "upvotes": int(upvote_span.get_text()),

            # Expected innerHtml ~= "18 comments"
            "comments": int(comment_span.get_text().split(" ")[0])
        }

class InvalidRequestException(Exception):
    pass


content_providers = [IndieHackerContentProvider()]
internet: Dict[str, List[Dict[str, object]]] = {}

for c in content_providers:
    resp = requests.get(c.getBaseWebsite())
    if resp.status_code != 200:
        raise InvalidRequestException("Invalid status code {} from website {}. {}".format(resp.url, c.getBaseWebsite, resp.reason))

    soup = bs4.BeautifulSoup(resp.content, "html.parser")
    internet[c.getContentId()] = c.getContent(soup)

print(internet)