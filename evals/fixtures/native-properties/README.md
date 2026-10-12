# Queue

Contract: FIFO order; popping an empty queue raises `IndexError`.
Existing seeded native property tests compare generated operation histories to
`collections.deque`. The command `python3 -m unittest discover -s tests -v`
replays all 50 recorded seeds deterministically. There are no external effects.
