class ParseError(Exception):
    def __init__(self, detail):
        self.detail = detail
