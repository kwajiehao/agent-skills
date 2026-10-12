# Independent review corrections

## Uninitialized submodule identity

Red: focused real-Git regressions showed a missing checkout falsely deleted and
an empty checkout falsely modified. A non-repository populated directory was
also incorrectly accepted as source. Result: 3 failures, 1 pass, 19 deselected.

The collector now verifies a submodule's own Git root before reading its status
or HEAD. Empty/missing uninitialized checkouts retain their gitlink; populated
non-repository content fails explicitly. Symlink/file replacements fail closed.

Green: three focused tests and two subtests passed, including a genuine initialized
submodule with unchanged/changed HEAD and a dirty internal tree rejection.

## Finding evidence labels

Browser red on the rendered example: `Error: finding evidence status visible`.
Cards previously displayed severity/confidence but omitted claim status. The
renderer now displays the status; the browser regression also substitutes inferred
and unknown findings and checks those labels. Protocol/setup failures (file URL
blocked, session closed) were setup failures, not the feature regression.

The retained final browser result and authoritative final runner results supply
green evidence. The older frozen walkthrough pilot precedes these review fixes.
