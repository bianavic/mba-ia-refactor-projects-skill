const crypto = require('crypto');

const KEY_LENGTH = 64;

function hashPassword(rawPassword) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derivedKey = crypto.scryptSync(rawPassword, salt, KEY_LENGTH);
    return `${salt}:${derivedKey.toString('hex')}`;
}

module.exports = { hashPassword };
