"""Small real SQLite target used to exercise the skill's recorder contract."""

import sqlite3


def initialize(path):
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE effects (job_id TEXT PRIMARY KEY, applications INTEGER NOT NULL)"
        )
        connection.commit()
    finally:
        connection.close()


def deliver(path, job_id, lose_ack=False):
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "INSERT OR IGNORE INTO effects VALUES (?, 1)", (job_id,)
        )
        connection.commit()
    finally:
        connection.close()
    if lose_ack:
        raise TimeoutError("acknowledgment lost after commit")


def applications(path, job_id):
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            "SELECT applications FROM effects WHERE job_id = ?", (job_id,)
        ).fetchone()
        return row[0] if row else 0
    finally:
        connection.close()


def parse_count(data):
    text = data.decode("ascii")
    if not text or any(char not in "0123456789" for char in text):
        raise ValueError("count must be unsigned decimal")
    return int(text)
