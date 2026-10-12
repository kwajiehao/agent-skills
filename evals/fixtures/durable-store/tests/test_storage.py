import unittest
from storage import save_value, load_value


class StorageTests(unittest.TestCase):
    def test_save_and_load(self):
        save_value("sample.json", {"count": 7})
        self.assertEqual(load_value("sample.json"), {"count": 7})
