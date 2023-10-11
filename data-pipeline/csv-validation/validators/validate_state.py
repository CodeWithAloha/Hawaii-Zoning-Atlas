from exceptions import InvalidStateException


def validate_state(val):
    
    if val != "HI":
        val = 'REPLACE_TEST'
        raise InvalidStateException("Invalid State. State should be HI.")
