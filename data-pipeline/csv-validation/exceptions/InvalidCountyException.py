class InvalidCountyException(Exception):
    def __init__(self, msg):
        super().__init__()
        self.__class__.__name__ = msg
