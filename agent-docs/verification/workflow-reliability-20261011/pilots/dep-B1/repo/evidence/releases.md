# parse-number releases

1.5.0: strict syntax option introduced, disabled by default.
1.6.0: strict syntax enabled by default. Callers accepting padded decimal
strings must explicitly pass `{strict: false}`.
