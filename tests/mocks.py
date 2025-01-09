"""Mock objects for testing"""

from unittest.mock import MagicMock


class MockServer:
    def __init__(self):
        self.tool = MagicMock()

    def run(self):
        pass


app = MockServer()
