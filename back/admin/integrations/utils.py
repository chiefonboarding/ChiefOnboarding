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
