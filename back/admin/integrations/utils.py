def get_value_from_notation(notation, value):
    # if we don't need to go into props, then just return the value
    if notation == "":
        return value

    notations = notation.split(".")
    for notation in notations:
        try:
            value = value[notation]
        except TypeError:
            # check if array
            if not isinstance(value, list):
                raise

            try:
                index = int(notation)
            except TypeError:
                # keep errors consistent, we are only expecting a KeyError
                raise KeyError

            try:
                value = value[index]
            except IndexError:
                # keep errors consistent, we are only expecting a KeyError
                raise KeyError

    return value


def convert_array_to_object(arr):
    return {item["key"]: item["value"] for item in arr}


def convert_object_to_array(obj):
    return [{"key": key, "value": value} for key, value in obj.items()]


def prepare_initial_data(obj):
    if isinstance(obj, dict):
        if obj.get("headers"):
            obj["headers"] = convert_object_to_array(obj["headers"])
        return obj

    return obj
