const assert = require('node:assert/strict');
const appPath = '/private/tmp/workflow-pilots-20261011.jYJEET/dep-B2/repo/app.js';
const {createRequire} = require('node:module');
const callerRequire = createRequire(appPath);
const {importCount} = callerRequire(appPath);
const identity = callerRequire('parse-number/package.json');
const cases = [['0', 0], ['7', 7], ['007', 7]];
let failures = 0;
console.log(JSON.stringify({package: identity, resolved: callerRequire.resolve('parse-number')}));
for (const [input, expected] of cases) {
  try {
    const actual = importCount({count: input});
    assert.equal(actual, expected);
    console.log(JSON.stringify({input, expected, actual, compatible: true}));
  } catch (error) {
    failures++;
    console.log(JSON.stringify({input, expected, error: `${error.name}: ${error.message}`, compatible: false}));
  }
}
// Validate the release-note mitigation without changing the application.
assert.equal(callerRequire('parse-number').parseNumber('007', {strict: false}), 7);
console.log('Explicit strict:false returns 7 for 007.');
process.exitCode = failures ? 1 : 0;
