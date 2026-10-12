# Dependency review

High risk; recommendation: **request-changes**. The resolved upgrade from parse-number 1.4.0 to 1.6.0 breaks the explicitly supported padded decimal input `007`. Through the unchanged application's actual `importCount` function, 1.4.0 returns `7`, while 1.6.0 throws `TypeError: invalid decimal`. Existing tests pass on both versions because they only assert an unpadded input.

## Target and dependency identity

- Repository: `/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo`.
- Base HEAD: `ddd80b30697b0ef87fff4cb39d08f401043df37b`.
- Head: uncommitted working tree; only `package-lock.json` changed.
- Declared range remains `^1.4.0` (`package.json:1`); resolved version changes 1.4.0 → 1.6.0 (`package-lock.json:1`, compared with `git show HEAD:package-lock.json`).
- Diff SHA-256: `860d0e6650feb6ca5505833909d83c6826c673ed8cf8f9a76a87ff7769d1daa0`.
- Working manifest SHA-256: `6db57cdfa50287612a69297bd13dc6cbe622b442311e3756612813de7ceecc1c`.
- Working lockfile SHA-256: `c2b1f9033c9ec3e77dae2d7bc002612955afeb2474d38c1a6310abdc22d20da5`.
- The final status/diff fingerprint matched the initial review target. No repository files were edited.

## Consequential impact

| Classification | Caller and requirement | Package evidence | Verified effect |
| --- | --- | --- | --- |
| Breaking | `app.js:4` calls `parseNumber(row.count)` with default options; `README.md:3–4` explicitly supports padded decimal strings, including `007`. | `evidence/releases.md:3–5` records strict syntax added in 1.5.0 and enabled by default in 1.6.0. `evidence/1.4.0/parse-number/index.js:2` accepts any digits; `evidence/1.6.0/parse-number/index.js:1–3` defaults `strict` to true and rejects a leading zero followed by another digit. | Real caller probe: old `007` → 7; new `007` → `TypeError: invalid decimal`. Error propagates through `importCount` because it has no catch. |

The exported CommonJS function remains available, and both artifact manifests require Node >=18 and retain `main: index.js`. They declare no transitive/peer/optional dependencies, overrides, installation scripts or native builds. The supplied minimal lockfiles list only this one package and no other changed resolution. These observations apply to the retained artifacts; registry integrity/provenance and a complete installation are not independently verified.

Search of the complete small project found one production package import and one direct wrapper call. No dynamic/plugin/configuration consumer was present in the supplied project. The 1.6.0 default change is reached directly by that caller.

## Verification

Runtime: Node v22.23.1, compatible with both artifacts' >=18 requirement. Each check ran in a separate Node process with `NODE_PATH` selecting the corresponding retained package extract. `probe.js` uses `createRequire` rooted at the actual `app.js`, reports the resolved package path and manifest identity, calls the actual `importCount`, and checks literal expected values for `0`, `7`, and `007`. It also verifies the documented `strict: false` mitigation directly against actual package code.

Commands were run from the repository:

```sh
NODE_PATH=/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo/evidence/1.4.0 node tests.js
NODE_PATH=/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo/evidence/1.6.0 node tests.js
NODE_PATH=/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo/evidence/1.4.0 node /private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/probe.js
NODE_PATH=/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo/evidence/1.6.0 node /private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/probe.js
```

| Check | Result |
| --- | --- |
| Existing test, 1.4.0 | Exit 0 |
| Existing test, 1.6.0 | Exit 0 |
| Caller probe, 1.4.0 | Exit 0; `0` → 0, `7` → 7, `007` → 7 |
| Caller probe, 1.6.0 | Exit 1; `0` → 0, `7` → 7, `007` throws `TypeError: invalid decimal` |
| Direct mitigation probe, both artifacts | `parseNumber('007', {strict: false})` → 7 |

Exact artifact entry-point SHA-256 hashes:

- 1.4.0: `d6e7a54e9a3b34b592eeb5d9407e0b6c48066bef5829055aad528d5b06dc7ddd`.
- 1.6.0: `0847ae191e97f5bae0122c609ce997fb5c3376adfd7d6afc703ed62fad05d7d5`.

`git diff --no-index evidence/1.4.0/parse-number evidence/1.6.0/parse-number` confirmed the release-note behavior in source. Its exit 1 means that source differences were found, not a failed test.

Coverage gap: `tests.js:3` only checks `'7'`; it does not assert the documented leading-zero behavior. No head-specific CI result was supplied or retrieved. All reported checks are local, offline checks against retained extracts, with no installation or download.

## Required correction

Preserve the import contract by passing `{strict: false}` at `app.js:4`, then add a regression assertion that `importCount({count: '007'})` equals `7` and run it against 1.6.0. Alternatively, defer the bump. The mitigation was verified against the new package, but no application or test change was made because this is a review request.

Evidence limitation: release notes and package sources were supplied locally, without external authenticity verification. That does not prevent the request-changes verdict: breakage is demonstrated against the exact retained old/new identities. No additional upstream check is needed to establish this incompatibility.
