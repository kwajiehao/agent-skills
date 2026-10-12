The accepted lost-acknowledgement retry guarantee is not trustworthy yet at
revision e7ff541688a844569299f06c9cf5bdd47579fb50.

Existing test_store.py covers one effect for single delivery. latest-run.json
reports 1000 generated cases, zero observed and zero checked lost-ack retries.
The required ordered sequence and oracle were never exercised. README.md:3 is
already authoritative; no semantic clarification is needed.

Static inspection identifies a probable product defect: store.py inserts
unconditionally, commits, then optionally raises TimeoutError. Retrying the same
job would insert another row. This is a static finding, not an executed
reproduction.

Recommended action: repair generator and durable-effect oracle before more
campaign time. Exercise a valid job with lose_ack=True in isolated SQLite, catch
the expected timeout, retry the same job_id, and independently check persisted
effect count one. Retain exact regression/replay and ordered observed/checked
coverage counters. Reject required zero coverage. Integrate with python3 -m
unittest discover -s tests -v. Initial smoke budget at most 30 seconds after
implementation is authorized; product repair needs separate implementation scope.

Assessment was read-only; no commands, campaigns, installs or file changes.
Existing latest-run.json preserved.

Provenance: retained content of /root/pilot_fuzz_gap's final response;
formatting simplified during archival. This is a partial trace, not a transcript.
