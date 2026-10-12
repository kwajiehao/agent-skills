const {Client} = require('opaque-client');
const client = new Client({timeout: 2000});
exports.fetch = id => client.get(id);
