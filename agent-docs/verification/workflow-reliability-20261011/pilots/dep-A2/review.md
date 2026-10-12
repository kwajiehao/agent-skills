# Dependency review: parse-number 1.4.0 → 1.6.0

Recommendation: **request changes**. Risk: **high**.

The lockfile-only upgrade breaks documented CSV input support. `importCount({count: "007"})` returns 7 with 1.4.0 but throws `TypeError("invalid decimal")` with 1.6.0. The adapter does not catch this exception. README.md:3–4 explicitly supports leading-zero decimal strings.

## Scope and usage audit

- package-lock.json:1 changes only the resolved parse-number version, 1.4.0 → 1.6.0.
- package.json:1 retains the compatible declared range ^1.4.0.
- app.js:1 imports the named parseNumber function via CommonJS.
- app.js:3–4 exposes importCount(row), passes row.count as the sole parseNumber argument, and directly returns the numeric result. It relies on default parsing behavior; no options or exception handling are present.
- tests.js:2–3 exercises importCount only with "7", expecting numeric 7.
- No other consumers, subclasses, exception handlers, or transitive package dependencies are present in the available project/package manifests.

## Change evidence and cross-reference

Local evidence/releases.md:3–5 documents the intervening releases: 1.5.0 introduced an optional strict syntax mode (default false); 1.6.0 enables it by default and instructs padded-string callers to specify {strict: false}. Comparing both local package sources confirms the implementation change.

| Classification | Dependency change | Project impact and reference |
| --- | --- | --- |
| BREAKING | Default acceptance changes from /^\\d+$/ to /^(0|[1-9]\\d*)$/; padded decimals now throw. | app.js:4 omits options, so documented counts "007", "00", and "012" fail instead of returning 7, 0, and 12. README.md:3–4 documents this supported path. |
| SAFE | Optional second argument {strict} is added; strict:false preserves permissive syntax. | Existing one-argument calls remain valid structurally. Passing {strict:false} at app.js:4 would address the observed break. No other options consumers exist. |

The source comparison finds no export rename, changed return conversion, new required argument, or exception type/message change. Both package manifests specify Node >=18 and neither declares transitive dependencies.

## Coverage and verification

- Existing tests pass under both versions using separate Node processes and NODE_PATH pointing at the supplied extracts.
- A contained regression assertion for the documented "007" input passes on 1.4.0 (exit 0) and fails on 1.6.0 (exit 1, TypeError at app.js:4).
- Additional isolated diagnostics confirm "00" and "012" regress, while "7", "0", and "12" still succeed; empty strings, negatives, and fractional strings remain rejected.
- Explicit 1.6.0 parseNumber("007", {strict:false}) returns 7.
- Node used: v22.23.1.
- High-risk coverage gap: tests.js:3 omits the documented padded-input path. Add regression coverage for padded positive counts and padded zero when updating the adapter.
- Remote CI status is unavailable offline. No CI configuration is present in the supplied project. These are local checks, not a claim of remote CI success.
- An exploratory in-process version-switch diagnostic was discarded because Node cached the old module; the evidence above uses separate processes and logs the exact resolved package source.

## Required follow-up

Preserve the documented contract by explicitly passing {strict:false}, and add padded-count regression coverage before approving the upgrade. Alternatively, retain the old version until a contract change is explicitly agreed. No fix was implemented because this request is a review.

Assessment is based on the supplied release notes and complete local package extracts; no network lookup, installation, or project mutation was performed.

