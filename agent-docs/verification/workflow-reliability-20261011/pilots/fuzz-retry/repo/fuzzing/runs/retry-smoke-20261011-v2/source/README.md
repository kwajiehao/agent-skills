# Job effect store

The accepted contract is one durable effect per `job_id`, including retry after
the acknowledgment of a committed effect was lost. `lose_ack=True` models that
boundary: the call commits and then raises `TimeoutError`.

Malformed amounts are outside this target's scope. Tests must use isolated local
SQLite paths. Current tests: `python3 -m unittest discover -s tests -v`.
