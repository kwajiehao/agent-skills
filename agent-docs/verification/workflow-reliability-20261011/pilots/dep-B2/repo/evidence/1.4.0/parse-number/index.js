exports.parseNumber = function parseNumber(value) {
  if (!/^\d+$/.test(value)) throw new TypeError('invalid decimal');
  return Number(value);
};
