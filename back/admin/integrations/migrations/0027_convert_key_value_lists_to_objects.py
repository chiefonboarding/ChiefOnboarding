from django.db import migrations


def is_key_value_list(value):
    return isinstance(value, list) and all(
        isinstance(item, dict) and "key" in item and "value" in item for item in value
    )


def convert(obj, key):
    """
    Convert `obj[key]` from [{"key": "test", "value": "hi"}] to {"test": "hi"}.
    Returns True if anything changed.
    """
    if not isinstance(obj, dict) or not is_key_value_list(obj.get(key)):
        return False
    obj[key] = {item["key"]: item["value"] for item in obj[key]}
    return True


def convert_manifest(manifest):
    """
    The integration builder used to save some key/value fields as a list of
    key/value items instead of an object. Returns True if the manifest changed.
    """
    if not isinstance(manifest, dict):
        return False

    changed = convert(manifest, "headers")

    exists = manifest.get("exists")
    changed |= convert(exists, "headers")
    changed |= convert(exists, "store_data")

    for step_type in ["form", "execute", "revoke"]:
        steps = manifest.get(step_type)
        if isinstance(steps, list):
            for step in steps:
                changed |= convert(step, "headers")

    return changed


def convert_key_value_lists(apps, schema_editor):
    Integration = apps.get_model("integrations", "Integration")
    for integration in Integration.objects.all().iterator():
        if convert_manifest(integration.manifest):
            integration.save(update_fields=["manifest"])


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0026_alter_integration_integration"),
    ]

    operations = [
        migrations.RunPython(convert_key_value_lists, migrations.RunPython.noop),
    ]
