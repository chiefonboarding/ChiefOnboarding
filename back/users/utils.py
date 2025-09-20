from django.utils.translation import gettext_lazy as _


class CompletedFormCheck:
    @property
    def completed_form_items(self):
        completed_blocks = []
        filled_items = [item["id"] for item in self.form]

        if getattr(self, "to_do", None) is not None:
            blocks = self.to_do.content["blocks"]
        else:
            blocks = self.preboarding.content["blocks"]

        for block in blocks:
            if (
                "data" in block
                and "type" in block["data"]
                and block["data"]["type"] in ["input", "text", "check", "upload"]
            ):
                item = next((x for x in filled_items if x == block["id"]), None)
                if item is not None:
                    completed_blocks.append(item)

        return completed_blocks


def parse_array_to_string(words):
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " " + _("and") + " " + words[-1]
