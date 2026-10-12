# Offline dependency upgrade review

High risk; verdict: request-changes. Against the retained package artifacts, upgrading parse-number from 1.4.0 to 1.6.0 breaks a documented invoice-import input: importCount({count: "007"}) returns 7 before the upgrade and throws TypeError("invalid decimal") afterward.

## Target and resolved versions

Reviewed base HEAD 0088070f74756dc9462dc913bf59f7be68c47479 against its working-tree changes. package.json:1 still declares ^1.4.0; the resolved package-lock.json:1 changes 1.4.0 to 1.6.0. The supplied lock lists only this package; no transitive changes or overrides are represented. Both package extracts identify themselves as parse-number with index.js as main and Node >=18. No scripts, peers, optional features or native builds are declared in these local package manifests. Runtime probes used Node v22.23.1.

The working tree also changes evidence/releases.md to state that upstream pages are unavailable offline. Those existing changes were preserved. Exact manifest, lock, caller, test and package-source SHA-256 hashes are retained in diagnostics.json. HEAD, status and hashes were checked again after probing; the reviewed files did not move.

## Consequential impact

| Effect | Caller/contract | Package evidence | Verification |
| --- | --- | --- | --- |
| Breaking: padded decimal strings are rejected | app.js:3–4 passes count without options; README.md:3–4 explicitly supports "007" as seven | evidence/1.4.0/parse-number/index.js:1–3 accepts digits; evidence/1.6.0/parse-number/index.js:1–3 defaults strict to true and excludes nonzero strings with leading zeroes | Real importCount returns 7 for "007" with 1.4.0; 1.6.0 throws TypeError("invalid decimal"). "00" similarly changes from 0 to TypeError. |
| Existing test misses the regression | tests.js:3 asserts only count "7" | Both package versions accept canonical "7" | The actual tests.js assertion ran and passed in each version-specific process. "0" also returned 0 in both probes. |

The upgraded implementation accepts "007" when explicitly given {strict:false}; this was verified against the real retained package. The current wrapper does not pass that option. A minimal corrective task is to preserve the documented input contract in the wrapper and add a regression assertion for "007", then rerun the ordinary test command against 1.6.0. No correction was implemented during this review.

## Exact verification

Two independent Node processes used NODE_PATH=repo/evidence/1.4.0 and NODE_PATH=repo/evidence/1.6.0, respectively. Each printed require.resolve("parse-number") and package metadata to prove which artifact loaded, required the real app.js and tests.js, and compared literal expected results for "7", "007", "0" and "00". Both diagnostic commands exited 0 because they captured errors as data; this is not a statement that every contract check passed. The new version produced two recorded contract mismatches. Full command text and JSON outputs are in diagnostics.json.

No dependencies were installed, no active environment or product file was changed, and no external mutation occurred. No CI evidence was available or claimed.

## Remaining uncertainty

The offline source comparison establishes this caller regression without release pages. It does not establish the full release interval's change list, published tarball provenance, registry identity/integrity, unrepresented transitive graph, or production-platform behavior. The minimal lock has no resolved URL or integrity hash, so the extracts cannot be cryptographically tied to a published registry artifact. These limits constrain the review's scope but do not erase the demonstrated violation of the local supported-input contract.

When upstream access becomes available, the smallest provenance check is to compare the 1.4.0 and 1.6.0 published package identities/integrities with the retained extracts and inspect their release/source evidence. Approval remains unsupported until the demonstrated caller breakage is corrected and covered.
