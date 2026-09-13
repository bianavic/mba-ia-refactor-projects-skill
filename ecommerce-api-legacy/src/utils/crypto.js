const crypto = require('crypto');

const KEY_LENGTH = 64;

function hashPassword(rawPassword) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derivedKey = crypto.scryptSync(rawPassword, salt, KEY_LENGTH);
    return `${salt}:${derivedKey.toString('hex')}`;
}

function verifyPassword(rawPassword, storedHash) {
    const [salt, hash] = storedHash.split(':');
    const derivedKey = crypto.scryptSync(rawPassword, salt, KEY_LENGTH);
    return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), derivedKey);
}

module.exports = { hashPassword, verifyPassword };
