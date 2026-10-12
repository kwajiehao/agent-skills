const {parseNumber} = require('parse-number');

function importCount(row) {
  return parseNumber(row.count);
}

module.exports = {importCount};
