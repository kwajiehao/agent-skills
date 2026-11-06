"""Read only deployment configuration and small backup receipts on Nebius."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys


def read_private(path):
    # Same ownership/symlink/size boundary as offsite_backup.state.read_private,
    # without importing its Pydantic model dependency on the login node.
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 65536:
            raise ValueError('unsafe or oversized private metadata')
        return stream.read(65537)


def snapshot(config, release):
    if config.get('site') != 'nebius' or type(config.get('max_backup_age_hours', 48)) is not int or config.get('max_backup_age_hours', 48) < 1:
        raise ValueError('invalid backup site/freshness configuration')
    state = Path(config['state_dir'])
    if not state.is_absolute() or '..' in state.parts:
        raise ValueError('invalid backup state directory')
    print("work-status-stage: small-receipts", file=sys.stderr, flush=True)
    tables = []
    for table in config['tables']:
        name = table['name']
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,79}', name):
            raise ValueError('invalid table name')
        entry = {"table": name}
        try:
            enrollment_path = Path(table['enrollment_file'])
            if not enrollment_path.is_absolute() or '..' in enrollment_path.parts:
                raise ValueError('invalid enrollment path')
            enrollment = json.loads(read_private(enrollment_path))
            entry["generation"] = enrollment["generation"]
            failure_path = state / name / "last_failure.json"
            entry["failure"] = json.loads(read_private(failure_path)) if failure_path.exists() else None
        except Exception as exc:
            entry["error"] = type(exc).__name__
        tables.append(entry)
    if not tables or len({t['table'] for t in tables}) != len(tables):
        raise ValueError('empty or duplicate table configuration')
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "site": config['site'],
            "release": Path(release).name, "max_backup_age_hours": config.get('max_backup_age_hours', 48),
            "storage": {"bucket": config['storage']['bucket'], "endpoint": config['storage']['endpoint'],
                        "prefix": config['storage'].get('prefix', 'lance-v1')}, "tables": tables}


def observe(mode, value, release=None):
    # No imports from the deployment's environment on the shared filesystem.
    # YAML parsing happens locally through the existing system safe parser.
    if mode == 'config':
        return {'config_yaml': read_private(Path(value)).decode('utf-8')}
    if mode == 'receipts':
        return snapshot(json.loads(value), release)
    raise ValueError('unsupported observer mode')


def main():
    signal.alarm(30)
    try:
        print(json.dumps(observe(*sys.argv[1:]), default=str))
        return 0
    except Exception as exc:
        # Error types are useful without leaking credentials or private SDK URLs.
        print(json.dumps({"error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
