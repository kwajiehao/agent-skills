# Dependency review: parse-number 1.4.0 → 1.6.0

**Risk: high. Recommendation: request changes.** The lockfile-only upgrade breaks a documented input contract: CSV counts containing leading zeroes now throw an uncaught TypeError instead of returning a number. Existing tests pass despite this regression.

## Scope and evidence

Reviewed the uncommitted package-lock.json change at line 1. package.json:1 continues to declare `parse-number: ^1.4.0`, which admits 1.6.0. Review conducted offline using evidence/releases.md and the complete local package extracts under evidence/1.4.0 and evidence/1.6.0; no installation or external write occurred.

## Usage audit

- app.js:1 imports the named CommonJS export `parseNumber`.
- app.js:3–4 exposes `importCount(row)` and directly returns `parseNumber(row.count)`, without an options argument or exception handler. Its caller expects a number.
- README.md:3–4 explicitly supports decimal strings with leading zeroes (`007` means seven).
- tests.js:2–3 exercises that same adapter with only `count: '7'` and expects numeric 7.
- No other call sites, subclasses, exception handlers, or transitive package dependencies appear in the available project/package evidence.

## Change analysis and impact

evidence/releases.md:3 records the addition of an optional strict syntax option in 1.5.0, initially disabled. Lines 4–5 record that 1.6.0 enables it by default and requires `{strict: false}` for padded decimals. The source diff confirms that the accepted pattern changes from `/^\d+$/` to `/^(0|[1-9]\d*)$/` by default. All substantive source changes in the available extracts are accounted for below.

| Classification | Change | Project reference and impact |
| --- | --- | --- |
| BREAKING | Strict syntax becomes the default; leading-zero decimal strings are rejected. | app.js:4 relies on the default. README.md:4 promises `007` support. Inputs `007` and `00` now throw `TypeError('invalid decimal')` instead of returning 7 and 0. There is no adapter catch. |
| SAFE | New optional second argument allows `{strict: false}`. | app.js:4 still accepts the function's one-required-argument signature. The option is a compatible escape hatch, but the project does not use it. |
| SAFE | Export, numeric conversion, invalid-input exception type/message, and Node engine requirement are unchanged. | app.js:1 named import remains valid; tests.js:3 still returns numeric 7. Both package manifests require Node >=18. Canonical decimals and previously invalid examples behave identically in local diagnostics. |

## Coverage and verification

- Existing `node tests.js` passed under both 1.4.0 and 1.6.0 using each extract as an isolated NODE_PATH, in separate Node v22.23.1 processes.
- Additional isolated diagnostics confirmed `007` → 7 and `00` → 0 under 1.4.0; both throw TypeError under 1.6.0. `7`, `0`, and `10` return the same values in both versions; `-1` and `abc` throw the same TypeError in both.
- A direct diagnostic confirmed `parseNumber('007', {strict: false})` returns 7 under 1.6.0. No project code was changed to try this option.
- High-risk coverage gap: tests.js:3 contains no padded-decimal input, so the documented adapter contract is untested. Add adapter-level cases for `007` and `00`, while retaining canonical and malformed-input coverage.
- CI status is unknown: no remote CI result was available. Local existing suite: PASS for both versions. Documented contract under candidate version: FAIL.
- An initial combined-process diagnostic was discarded because Node's module resolution cache retained the old dependency for the importer; all reported comparison results above come from fresh isolated processes with the resolved package paths verified.

## Recommendation

Request changes before merging. Update app.js:4 to pass `{strict: false}` to retain the existing supported input contract and add adapter regression tests for padded counts, then rerun the suite with 1.6.0. Alternatively defer the bump. The review itself leaves project files unchanged.
