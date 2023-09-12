def get_value_from_notation(notation, value):
    # if we don't need to go into props, then just return the value
    if notation == "":
        return value

    notations = notation.split(".")
    for notation in notations:
        value = value[notation]
    return value
