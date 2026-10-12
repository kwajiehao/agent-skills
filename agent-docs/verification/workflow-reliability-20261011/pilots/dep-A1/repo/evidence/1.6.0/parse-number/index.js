exports.parseNumber = function parseNumber(value, {strict = true} = {}) {
  const pattern = strict ? /^(0|[1-9]\d*)$/ : /^\d+$/;
  if (!pattern.test(value)) throw new TypeError('invalid decimal');
  return Number(value);
};
