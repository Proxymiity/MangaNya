from exceptions import ModelValidationError


def db_sanitize(val):
    return "".join(x for x in val if x.isalnum() or x == "_")


def validate_model(obj, properties, use_raise=True):
    for x in properties:
        y = obj.__dict__.get(x)
        if y:
            pass
        else:
            if use_raise:
                raise ModelValidationError(x)
            return False
    return True
