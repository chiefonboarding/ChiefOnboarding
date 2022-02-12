from crispy_forms.layout import Field
from crispy_forms.utils import TEMPLATE_PACK


class WYSIWYGField(Field):
    template = "wysiwyg_field.html"


class MultiSelectField(Field):
    template = "multi_select_field.html"


class FieldWithExtraContext(Field):
    # Copied from SO, this allows us to add extra content to the field (such as the file object)
    # https://stackoverflow.com/a/41189149
    extra_context = {}

    def __init__(self, *args, **kwargs):
        self.extra_context = kwargs.pop("extra_context", self.extra_context)
        super().__init__(*args, **kwargs)

    def render(
        self,
        form,
        form_style,
        context,
        template_pack=TEMPLATE_PACK,
        extra_context=None,
        **kwargs
    ):
        if self.extra_context:
            extra_context = (
                extra_context.update(self.extra_context)
                if extra_context
                else self.extra_context
            )
        return super().render(
            form, form_style, context, template_pack, extra_context, **kwargs
        )

class UploadField(FieldWithExtraContext):
    template = "upload_field.html"


