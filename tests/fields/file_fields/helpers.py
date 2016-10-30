class MockFile:
    def __init__(self, name='', size=0, url=''):
        self.name = name
        self.size = size
        self.url = url

    def __eq__(self, other):
        return (
            isinstance(other, MockFile) and
            self.name == other.name and
            self.size == other.size and
            self.url == other.url
        )
