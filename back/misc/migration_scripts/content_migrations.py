from django.db import migrations, router


class RunPythonWithArguments(migrations.RunPython):
    # Credits: https://stackoverflow.com/a/62899691
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop("context", {})
        super().__init__(*args, **kwargs)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from_state.clear_delayed_apps_cache()
        if router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):
            self.code(from_state.apps, schema_editor, **self.context)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass


def migrate_wysiwyg_field(apps, schema_context, **context):
    Model = apps.get_model(context["app"], context["model"])
    for item in Model.objects.all():
        new_json = []
        for block in item.content.all():
            if block.type == "p":
                new_json.append({"type": "paragraph", "data": {"text": block.content}})
            if block.type in ["h1", "h2", "h3"]:
                level = int(block.type.replace("h", ""))
                new_json.append(
                    {"type": "header", "data": {"text": block.content, "level": level}}
                )
            if block.type == "quote":
                new_json.append(
                    {
                        "type": block.type,
                        "data": {
                            "text": block.content,
                            "caption": "",
                            "alignment": "left",
                        },
                    }
                )
            if block.type == "youtube":
                new_json.append(
                    {
                        "type": "embed",
                        "data": {
                            "service": "youtube",
                            "source": block.content,
                            "embed": block.content,
                            "width": 580,
                            "height": 320,
                            "caption": "",
                        },
                    }
                )
            if block.type in ["ul", "ol"]:
                new_json.append(
                    {
                        "type": "list",
                        "data": {
                            "style": "unordered" if block.type == "ul" else "ordered",
                            "items": [item for item in block.items],
                        },
                    }
                )
            if block.type == "hr":
                new_json.append({"type": "delimiter", "data": {}})
            if block.type == "file" or block.type == "video":
                for file in block.files.all():
                    new_json.append(
                        {
                            "type": "attaches",
                            "data": {
                                "file": {
                                    "url": "",
                                    "uuid": str(file.uuid),
                                    "id": file.id,
                                    "name": file.name,
                                    "extension": file.ext,
                                },
                                "title": file.name,
                            },
                        }
                    )
            if block.type == "image":
                new_json.append(
                    {
                        "type": "image",
                        "data": {
                            "file": {"url": "", "id": block.files.all()[0].id},
                            "caption": "",
                            "withBorder": False,
                            "withBackground": False,
                            "stretched": True,
                        },
                    }
                )
            if block.type == "question":
                new_json.append(
                    {
                        "type": "question",
                        "items": [
                            {"id": item["id"], "text": item["text"]}
                            for item in block.items
                        ],
                        "answer": block.answer,
                        "content": block.content,
                    }
                )

        item.content_json = {"time": 0, "blocks": new_json}
        item.save()


# used for prebaording and todo items
# This is ugly. I know. But it works and will only be used once or twice
def migrate_forms_to_wysiwyg(apps, schema_context, **context):
    Model = apps.get_model(context["app"], context["model"])
    for item in Model.objects.all():
        content = item.content
        for form_item in item.form:
            if form_item["type"] == "select":
                continue
            if form_item["type"] in ["text", "input", "upload"]:
                content["blocks"].append(
                    {
                        "type": "form",
                        "data": {
                            "type": form_item["type"],
                            "text": form_item["text"],
                        },
                    }
                )
            else:
                content["blocks"].append(
                    {
                        "type": "paragraph",
                        "data": {
                            "text": form_item["text"],
                            "caption": "",
                            "alignment": "left",
                        },
                    }
                )

                if "options" in form_item:
                    key = "options"
                else:
                    key = "items"

                for sub_item in form_item[key]:
                    content["blocks"].append(
                        {
                            "type": "form",
                            "data": {
                                "type": form_item["type"],
                                "text": sub_item["name"],
                            },
                        }
                    )

        item.content = content
        item.save()
