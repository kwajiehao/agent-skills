const assert = require('node:assert/strict');
const {importCount} = require('./app');
assert.equal(importCount({count: '7'}), 7);
