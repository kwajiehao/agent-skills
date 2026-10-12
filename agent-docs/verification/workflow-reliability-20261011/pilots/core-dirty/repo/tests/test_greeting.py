import unittest
from greeting import greet


class GreetingTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_surrounding_whitespace(self) -> None:
        for name in ("  Ada  ", "\tAda\t", "\nAda\n", " \t\nAda\n\t "):
            with self.subTest(name=name):
                self.assertEqual(greet(name), "Hello, Ada!")

    def test_internal_whitespace(self) -> None:
        self.assertEqual(greet("  Ada  Lovelace  "), "Hello, Ada  Lovelace!")
