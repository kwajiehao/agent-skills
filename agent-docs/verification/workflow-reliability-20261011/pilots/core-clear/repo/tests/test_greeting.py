import unittest
from greeting import greet


class GreetingTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_surrounding_whitespace(self) -> None:
        self.assertEqual(greet(" \tAda\n "), "Hello, Ada!")

    def test_interior_whitespace(self) -> None:
        self.assertEqual(greet("  Ada  Lovelace  "), "Hello, Ada  Lovelace!")
