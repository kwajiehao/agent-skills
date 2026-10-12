# Dependency review: high risk, request-changes

The lockfile upgrade demonstrably breaks supported CSV count inputs. `importCount({count: '007'})` returns `7` under the retained parse-number 1.4.0 artifact and throws `TypeError: invalid decimal` under 1.6.0. Correct the adapter to preserve its documented input contract and add regression coverage before accepting the upgrade.

## Target and resolved change

- Repository: `/private/tmp/workflow-pilots-20261011.jYJEET/dep-B1/repo`.
- Base HEAD: `dcf0b9517fb4ccb627d1ad22b92f9c05f51cab95`; head is the uncommitted lockfile change.
- Declared range remains `parse-number: ^1.4.0`; resolved version changes from 1.4.0 to 1.6.0 (`package-lock.json:1`). No other lockfile package entries or changes are present. No overrides or optional dependencies are declared.
- Manifest SHA-256: `6db57cdfa50287612a69297bd13dc6cbe622b442311e3756612813de7ceecc1c`.
- Reviewed lockfile SHA-256: `c2b1f9033c9ec3e77dae2d7bc002612955afeb2474d38c1a6310abdc22d20da5`.
- HEAD, manifest, lockfile, and git status were unchanged at the final freshness check. Only the pre-existing lockfile modification remains.

## Consequential impact

| Classification | Caller / contract evidence | Package evidence | Result |
| --- | --- | --- | --- |
| Breaking | `app.js:4` calls `parseNumber(row.count)` without options. `README.md:3`–4 documents padded decimal input such as `007`. | `evidence/releases.md:3`–5: 1.5.0 introduces strict syntax off by default; 1.6.0 enables it. `evidence/1.6.0/parse-number/index.js:1`–3 defaults `strict=true` and rejects padded strings. Old source accepts all digit strings (`evidence/1.4.0/parse-number/index.js:2`). | Supported `007` and `00` now throw an uncaught TypeError instead of returning 7 and 0. |

The only dependency import is the adapter's CommonJS import in `app.js:1`. Both retained package manifests name parse-number, expose `index.js`, and require Node >=18; no dependencies, exports map, peer dependencies, or install scripts are declared. Available Node v22.23.1 satisfies that requirement. No additional runtime/toolchain change is evidenced by these extracts.

## Verification

From the repository, existing tests were run against both real extracts using isolated module lookup, with no installation:

```sh
NODE_PATH="$PWD/evidence/1.4.0" node tests.js
NODE_PATH="$PWD/evidence/1.6.0" node tests.js
```

Both passed. `tests.js:3` checks only the unpadded value `7`; it misses the documented padded input behavior.

A caller-shaped Node probe used the same NODE_PATH values, asserted `require.resolve('parse-number')` matched the exact artifact path, loaded the actual `./app` adapter, and compared literal outputs/errors with `assert.deepEqual`:

| Input | 1.4.0 | 1.6.0 |
| --- | --- | --- |
| `7` | 7 | 7 |
| `007` | 7 | TypeError: invalid decimal |
| `0` | 0 | 0 |
| `00` | 0 | TypeError: invalid decimal |
| `10` | 10 | 10 |

Both probe expectation assertions passed. These confirm the regression, not compatibility. Source SHA-256 identities were `d6e7a54e9a3b34b592eeb5d9407e0b6c48066bef5829055aad528d5b06dc7ddd` (1.4.0) and `0847ae191e97f5bae0122c609ce997fb5c3376adfd7d6afc703ed62fad05d7d5` (1.6.0).

A further real-package probe confirmed 1.6.0 preserves `007 => 7` and `00 => 0` when explicitly passed `{strict:false}`. This validates the smallest corrective direction, but the adapter was not changed. Add padded-input assertions to the adapter tests and rerun against 1.6.0 after that correction.

`git diff --check` passed. No CI evidence was supplied or consulted. No installs, external requests, or project writes were performed.

## Evidence limits

This is an offline assessment based on the retained package extracts and release evidence. The minimal lockfile has no registry URL or integrity digest, so registry provenance and a complete clean install were not verified. Those limits do not prevent a request-changes verdict: the supplied exact-version implementations demonstrate a failure of the explicit project contract.
