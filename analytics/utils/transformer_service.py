import json
from html.parser import HTMLParser

from backend_shared.schemas.ingestion_schema import ContentRequest


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []

    def handle_data(self, data):
        self.texts.append(data)

    def get_text(self):
        return "".join(self.texts)


# Function to recursively extract text from nodes
def extract_text(nodes, text_list):
    for node in nodes:
        if node.get("kind") == "text":
            text_list.append(node.get("text", ""))
        elif node.get("nodes"):
            extract_text(node["nodes"], text_list)


def transform_to_content_request(article: dict, brand) -> ContentRequest:
    """
    Transform an article to a ContentRequest object. How it is transformed depends on the brand.

    Args:
        article (dict): Article data.
        brand (str): Brand name.

    Returns:
        ContentRequest: ContentRequest object.
    """

    if brand == "Keskisuomalainen":
        if article["paywall_status"] == "paidStar":
            article["paywall_status"] = "paid-star"
        elif article["paywall_status"] == "":
            article["paywall_status"] = "free"

        # Extract tags safely
        tags = []
        if "tags" in article and article["tags"]:
            if isinstance(article["tags"], list):
                tags = article["tags"]
            else:
                tags = article["tags"].split(",")

        # Extract authors safely
        authors = []
        if "authors" in article and article["authors"]:
            if isinstance(article["authors"], list):
                authors = article["authors"]
            else:
                authors = article["authors"].split(",")

        return ContentRequest(
            metadata={
                "count_words": str(article["count_words"]),
                "count_chars": str(article["count_chars"]),
                "count_paragraphs": str(article["count_paragraphs"]),
                "count_images": str(article["count_images"]),
                "count_quotes": str(article["count_quotes"]),
                "count_facts": str(article["count_facts"]),
                "count_embeds": str(article["count_embeds"]),
            },
            id=str(article["id"]),
            title=article["title"],
            kicker="",
            body=article["body"],
            ingress=article["lead"],
            url=article["article_url"],
            paywall_status=article["paywall_status"],
            category=article["category"],
            domain=article["title_code"],
            brand=article["source"],
            content_type=article["content_type"].lower(),
            partner=None,
            tags=tags,
            authors_writers=authors,
            authors_photographers=[],
            publish_date=article["publish_date"],
            update_date=article["update_date"],
        )

    elif brand == "A-lehti":
        temp_body = ""
        if article["body"]["plain"] != "":
            temp_body = article["body"]["plain"]
        elif article["body"]["html"] != "":
            parser = MyHTMLParser()
            # Feed the HTML string to the parser
            parser.feed(article["body"]["html"])
            # Get the extracted text
            temp_body = parser.get_text()
        elif article["body"]["raw"] != "":
            data = json.loads(article["body"]["raw"])
            # List to store extracted text
            texts = []
            # Calling the function with the initial nodes
            extract_text(data["nodes"], texts)
            # Joining the list into a single string with newline separator
            temp_body = "\n".join(texts)

        if "type" in article.keys() and article["type"] != "Article":
            return "Not an article"
        else:
            article["type"] = "article"

        if "slug" in article.keys():
            article["slug"] = article["slug"]
        else:
            article["slug"] = ""

        if "readingTime" in article.keys():
            article["readingTime"] = str(article["readingTime"])
        else:
            article["readingTime"] = "0"

        if "metadata" in article.keys():
            article["metadata"] = article["metadata"]["commercialType"]
        else:
            article["metadata"] = ""

        if "kicker" in article.keys():
            article["kicker"] = article["kicker"]
        else:
            article["kicker"] = ""

        if "category" in article.keys():
            article["category"] = article["category"]["title"]
        else:
            article["category"] = ""

        if "restrictAccessBy" in article.keys():
            if article["restrictAccessBy"] == "null":
                article["restrictAccessBy"] = "free"
            else:
                article["restrictAccessBy"] = "paid"
        else:
            article["restrictAccessBy"] = "free"

        if "brand" in article.keys() and article["brand"] != None:
            article["brand"] = article["brand"]["name"]
        else:
            article["brand"] = "None"

        if "partner" in article.keys() and article["partner"] != None:
            article["partner"] = article["partner"]["name"]
        else:
            article["partner"] = "None"

        authors = []
        if "writers" in article.keys() and len(article["writers"]) > 0:
            for writer in article["writers"]:
                authors.append(writer["name"])

        return ContentRequest(
            metadata={
                "slug": article["slug"],
                "reading_time": str(article["readingTime"]),
                "commercial_type": article["metadata"],
            },
            id=str(article["id"]),
            title=article["title"],
            kicker=article["kicker"],
            body=temp_body,
            ingress="",
            url="",
            paywall_status=article["restrictAccessBy"],
            category=article["category"],
            domain="A-lehti",
            brand=article["brand"],
            content_type=article["type"],
            partner=article["partner"],
            tags=[],
            authors_writers=authors,
            authors_photographers=[],
            publish_date=article["publishedAt"],
            update_date=article["publishedAt"],
        )

    else:
        return "Not a valid brand"
