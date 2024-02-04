from functools import wraps

from .util import is_unsigned_byte


def validate_unsigned_byte_command(func):
    """`self` is arg0 and command byte is arg1."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_unsigned_byte(args[1]):
            raise ValueError("'{}' is not an unsigned byte.".format(args[1]))
        else:
            return func(*args, **kwargs)

    return wrapper
