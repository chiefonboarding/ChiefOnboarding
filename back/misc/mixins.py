from misc.urlparser import URLParser

from misc.models import File


class ContentMixin:

    def _prep_inner_text_for_slack(self, text):
        replacements = (
            ("<p>", ""),
            ("</p>", ""),
            ("<br>", ""),
            ("<br />", ""),
            ("<b>", "*"),
            ("</b>", "*"),
            ("<strong>", "*"),
            ("</strong>", "*"),
            ("</i>", "_"),
            ("<i>", "_"),
            ("<em>", "_"),
            ("</em>", "_"),
            ("<u>", ""),
            ("</u>", ""),
            ("<code>", "`"),
            ("</code>", "`"),
            ("</strike>", "~"),
            ("<strike>", "~"),
        )
        for r in replacements:
            text = text.replace(*r)
            parser = URLParser()
            parser.feed(text)
            for link in parser.get_links():
                text = text.replace(
                    link["original_tag"] + link["text"] + "</a>",
                    "<" + link["url"] + "|" + link["text"] + ">",
                )
        return text

    def to_slack_block(self, user, json_field='content', **kwargs):
        if not hasattr(self, json_field):
            raise Exception("Field does not exist")

        blocks = getattr(self, json_field)["blocks"]

        # Is a course item with questions
        if "data" not in blocks[0]:
            slack_blocks = []
            for idx, question in enumerate(blocks):
                slack_options = []
                for option in question["items"]:
                    slack_options.append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": option["text"],
                                "emoji": True
                            },
                            "value": option["id"]
                        }
                    )


                slack_blocks.append({
                    "type": "input",
                    "block_id": f"item-{idx}",
                    "element": {
                        "type": "radio_buttons",
                        "options": slack_options,
                        "action_id": f"item-{idx}"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": question["content"],
                        "emoji": True
                    }
                })

            return slack_blocks

        slack_blocks = []
        for item in blocks:
            if "text" in item["data"]:
                if item["data"]["text"] == "":
                    item["data"]["text"] = "-"
                text = user.personalize(item["data"]["text"])
                item["data"]["text"] = self._prep_inner_text_for_slack(text)
            if "items" in item["data"]:
                for list_item in item["data"]["items"]:
                    if list_item == "":
                        list_item = "-"
                    text = user.personalize(list_item)
                    item["data"]["text"] = self._prep_inner_text_for_slack(text)
            if "text" in item["data"]:
                default_text = item["data"]["text"]
            else:
                default_text = ""

            slack_block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": default_text},
            }
            if item["type"] == "header":
                slack_block["text"]["text"] = "*" + item["data"]["text"] + "*"
            elif item["type"] == "quote":
                slack_block = {
                    "type": "context",
                    "elements": {
                        "text": {
                            "type": "mrkdwn",
                            "text": item["data"]["text"] + "\n" + item["data"]["caption"],
                        }
                    },
                }
            elif item["type"] == "list" and item["data"]["style"] == "ordered":
                ul_list = ""
                for idx, list_item in enumerate(item["data"]["items"]):
                    ul_list += str(idx + 1) + ". " + user.personalize(list_item) + "\n"
                slack_block["text"]["text"] = ul_list
            elif item["type"] == "list" and item["data"]["style"] == "unordered":
                ol_list = ""
                for list_item in item["data"]["items"]:
                    ol_list += "* " + user.personalize(list_item) + "\n"
                slack_block["text"]["text"] = ol_list
            elif item["type"] == "delimiter":
                slack_block = {"type": "divider"}
            elif item["type"] == "file":
                files_text = "<" + File.objects.get(id=item["data"]["file"]["id"]).get_url() + "|Watch video>"
                slack_block["text"]["text"] = files_text
            elif item["type"] == "video":
                files_text = (
                    "<"
                    + File.objects.get(id=item["data"]["file"]["id"]).get_url()
                    + "|"
                    + item["file"]["name"]
                    + "> "
                )
                slack_block["text"]["text"] = files_text
            elif item["type"] == "image":
                slack_block = {
                    "type": "image",
                    "image_url": File.objects.get(id=item["data"]["file"]["id"]).get_url(),
                    "alt_text": "image",
                }
            elif item["type"] == "question":
                options = []
                for i in item["items"]:
                    options.append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": user.personalize(i["text"]),
                                "emoji": True,
                            },
                            "value": i["id"],
                        }
                    )
                slack_block = {
                    "type": "input",
                    "block_id": str(item["id"]),
                    "element": {
                        "type": "static_select",
                        "action_id": str(item["id"]),
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select answer",
                            "emoji": True,
                        },
                        "options": options,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": item["data"]["text"],
                        "emoji": True,
                    },
                }
            if item["type"] == "form":
                if item["data"]["type"] == "input":
                    slack_block = {
                        "type": "input",
                        "block_id": str(item["id"]),
                        "element": {"type": "plain_text_input", "action_id": str(item["id"])},
                        "label": {
                            "type": "plain_text",
                            "text": item["data"]["text"],
                            "emoji": True,
                        },
                    }
                if item["data"]["type"] == "text":
                    slack_block = {
                        "type": "input",
                        "block_id": str(item["id"]),
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True,
                            "action_id": str(item["id"]),
                        },
                        "label": {
                            "type": "plain_text",
                            "text": item["data"]["text"],
                            "emoji": True,
                        },
                    }
            slack_blocks.append(slack_block)
        return slack_blocks
