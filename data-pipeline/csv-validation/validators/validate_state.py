from exceptions import InvalidStateException


def validate_state(val):
    if val != "HI":
        raise InvalidStateException
