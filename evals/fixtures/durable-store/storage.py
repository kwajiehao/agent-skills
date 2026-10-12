_values = {}


def save_value(path, value):
    _values[str(path)] = value


def load_value(path):
    return _values.get(str(path))
