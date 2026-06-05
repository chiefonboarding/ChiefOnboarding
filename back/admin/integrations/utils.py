def _tokenize_notation(notation):
    # split on '.' but keep [...] groups intact, so values inside a filter
    # expression (which may themselves contain '.', e.g. emails) aren't split
    tokens = []
    buf = ""
    depth = 0
    for ch in notation:
        if ch == "[":
            depth += 1
            buf += ch
        elif ch == "]":
            depth -= 1
            buf += ch
        elif ch == "." and depth == 0:
            if buf:
                tokens.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def get_value_from_notation(notation, value):
    # if we don't need to go into props, then just return the value
    if notation == "":
        return value

    for token in _tokenize_notation(notation):
        # filter form: optional_key[field=expected] - pick first list entry
        # whose `field` equals `expected`. Useful when the upstream API returns
        # an unfiltered list (e.g. Bitwarden /public/members).
        if "[" in token and token.endswith("]"):
            list_key, _, filter_expr = token.partition("[")
            filter_expr = filter_expr[:-1]

            if list_key:
                try:
                    value = value[list_key]
                except (KeyError, TypeError):
                    raise KeyError

            if "=" not in filter_expr or not isinstance(value, list):
                raise KeyError

            field, _, expected = filter_expr.partition("=")
            for item in value:
                if isinstance(item, dict) and str(item.get(field, "")) == expected:
                    value = item
                    break
            else:
                raise KeyError
            continue

        try:
            value = value[token]
        except TypeError:
            if not isinstance(value, list):
                raise KeyError

            try:
                index = int(token)
            except (TypeError, ValueError):
                raise KeyError

            try:
                value = value[index]
            except (TypeError, ValueError, IndexError):
                raise KeyError

    return value


def convert_array_to_object(arr):
    return {item["key"]: item["value"] for item in arr}


def convert_object_to_array(obj):
    return [{"key": key, "value": value} for key, value in obj.items()]


def prepare_initial_data(obj):
    if isinstance(obj, dict):
        if obj.get("headers") and not isinstance(obj["headers"], list):
            obj["headers"] = convert_object_to_array(obj["headers"])
        return obj

    return obj
