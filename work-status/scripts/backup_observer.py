"""Read only deployment configuration and small backup receipts on Nebius."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sys


def observe(release, config_path):
    os.chdir(release)
    sys.path.insert(0, release)
    print("work-status-stage: config-import", file=sys.stderr, flush=True)
    # Avoid monitoring/source imports: they load the full Lance runtime.
    from devops.offsite_backup.config import load_config
    from devops.offsite_backup.state import read_private

    config = load_config(Path(config_path))
    print("work-status-stage: small-receipts", file=sys.stderr, flush=True)
    tables = []
    for table in config.tables:
        entry = {"table": table.name}
        try:
            enrollment = json.loads(read_private(table.enrollment_file, 65536))
            entry["generation"] = enrollment["generation"]
            failure_path = config.state_dir / table.name / "last_failure.json"
            entry["failure"] = json.loads(read_private(failure_path, 65536)) if failure_path.exists() else None
        except Exception as exc:
            entry["error"] = type(exc).__name__
        tables.append(entry)
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "site": config.site,
            "release": Path(release).name, "max_backup_age_hours": config.max_backup_age_hours,
            "storage": {"bucket": config.storage.bucket, "prefix": config.storage.prefix,
                        "endpoint": config.storage.endpoint}, "tables": tables}


def main():
    signal.alarm(45)
    try:
        print(json.dumps(observe(*sys.argv[1:]), default=str))
        return 0
    except Exception as exc:
        # Error types are useful without leaking credentials or private SDK URLs.
        print(json.dumps({"error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
