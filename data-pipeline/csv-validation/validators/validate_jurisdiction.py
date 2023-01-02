from exceptions import InvalidJurisdictionException

# TODO: Verify jurisdiction based on the file passed in
# TODO: Account for okinas in Hawaii? 
def validate_jurisdiction(val):
  jurisdictions = ["Hawaii", "Kauaʻi", "Maui", "Honolulu"]
  if val not in jurisdictions:
    raise InvalidJurisdictionException