from crispy_forms.layout import Field
from crispy_forms.utils import TEMPLATE_PACK
from django import forms


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


class ModelChoiceFieldWithCreate(forms.ModelChoiceField):
    def prepare_value(self, value):
        # Forcing pk value in this case. Otherwise "selected" will not work
        if hasattr(value, "_meta"):
            return value.pk
        return super().prepare_value(value)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"

            # This needs to be refactored. If a user enters a number for this field,
            # then it will pick a category instead. Warning added to help_text
            try:
                value = self.queryset.get(pk=value).name
            except:
                pass

            value = self.queryset.get(**{key: value})
        except (ValueError, TypeError):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        except self.queryset.model.DoesNotExist:
            value = self.queryset.create(**{key: value})
        return value
