from doctest import UnexpectedException
import bs4
from typing import Dict, List


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


class HackerNewsContentProvider(InternetContentProvider):

    def getBaseWebsite(self) -> str:
        return "https://news.ycombinator.com"

    def getContentId(self) -> str:
        return "hackerNews-news"

    def getContent(self, page: bs4.BeautifulSoup) -> List[Dict[str, object]]:
        contentList = page.find("table", class_="itemlist").find_all("tr")
        i = 0
        entries = []

        # Ignore last two lines, they are just extra padding <tr> elements
        while i<len(contentList)-2:
            main_line = contentList[i]
            score_metadata = contentList[i+1]
            
            # Third element is a spacer <tr>
            i+=3

            entries.append(self.convertItemPost(main_line, score_metadata))

        return entries
        
    def convertItemPost(self, main_line: bs4.Tag, score_metadata: bs4.Tag) -> Dict[str, object]:
        """ Converts a single post from HackerNews.

        main_line: Table row line contains the link and title of the post.
        score_metadata: 
            Example: `95 points by atomiomi 12 hours ago | hide | 71 comments`
        """
        title_link = main_line.find("a", class_="titlelink")

        return {
            "title": title_link.get_text().strip(),
            "full_link": title_link.get('href'),
            "upvotes": self.getUpvotes(score_metadata),
            "comments": self.getCommentCount(score_metadata),

            # Expected key title="2022-04-27T09:28:57"
            "published": score_metadata.find("span", class_="age").get("title")
        }
    
    def getUpvotes(self, score_metadata: bs4.Tag) -> int:
        upvote_span = score_metadata.find("span", class_="score")
        if upvote_span:
            # Expected innerHtml ~= "415 points"
            return int(upvote_span.get_text().split(" ")[0])
        else:
            return 0 

    def getCommentCount(self, score_metadata: bs4.Tag) -> int:
        links = score_metadata.find_all("a")
        if len(links) == 4:        
            # Expected innerHtml ~= "289 comments"
            return int(links[-1].get_text().split("\xa0")[0])
        else:
            return 0