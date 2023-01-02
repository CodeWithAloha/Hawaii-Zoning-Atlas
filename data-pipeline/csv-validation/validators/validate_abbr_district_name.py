# TODO: Determine constraints for abbreviated district names
# TODO: Verify that abbreviated district names can't be only numbers
def validate_abbr_district_name(val):
    if not isinstance(val, str) or val.isnumeric():
        raise ValueError
