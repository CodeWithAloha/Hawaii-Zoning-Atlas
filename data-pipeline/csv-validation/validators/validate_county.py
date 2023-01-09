from exceptions import InvalidCountyException

# TODO: Verify jurisdiction based on the file passed in
# TODO: Account for okinas in Hawaii?
def validate_county(val):
    counties = ["Hawaii", "Kauaʻi", "Maui", "Honolulu"]
    if val not in counties:
        raise InvalidCountyException("Invalid County, county should be: Hawaii, Kauaʻi, Maui, or Honolulu")
