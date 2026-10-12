import random
import unittest
from collections import deque
from queue import Queue


class QueueProperties(unittest.TestCase):
    def test_generated_histories_against_deque(self):
        for seed in range(50):
            rng, target, model = random.Random(seed), Queue(), deque()
            for _ in range(200):
                if not model or rng.random() < .6:
                    item = rng.randrange(-100, 100)
                    target.push(item)
                    model.append(item)
                else:
                    self.assertEqual(target.pop(), model.popleft())
            while model:
                self.assertEqual(target.pop(), model.popleft())
            with self.assertRaises(IndexError):
                target.pop()
