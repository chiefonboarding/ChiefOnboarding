from html.parser import HTMLParser
from xml.etree import cElementTree as etree


class URLParser(HTMLParser):
    def reset(self):
        HTMLParser.reset(self)
        self.links = []
        self.link = {}
        self.found_link = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            builder = etree.TreeBuilder()
            builder.start(tag, dict(attrs))
            builder.end(tag)
            full_tag = builder.close()
            self.link = {
                "original_tag": etree.tostring(full_tag).decode("utf-8").replace(" /", ""),
                "url": dict(attrs)["href"],
                "text": "",
            }
            self.found_link = True

    def handle_data(self, data):
        if self.found_link:
            self.found_link = False
            self.link["text"] = data
            self.links.append(self.link)

    def get_links(self):
        return self.links
