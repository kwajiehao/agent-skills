import sqlite3


def apply_job(path, job_id, amount, lose_ack=False):
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS effects(job_id TEXT, amount INTEGER)")
        db.execute("INSERT INTO effects VALUES (?, ?)", (job_id, amount))
        db.commit()
        if lose_ack:
            raise TimeoutError("acknowledgement lost after commit")
        return "applied"
    finally:
        db.close()


def effect_count(path, job_id):
    with sqlite3.connect(path) as db:
        return db.execute("SELECT COUNT(*) FROM effects WHERE job_id=?", (job_id,)).fetchone()[0]
