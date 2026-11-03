// Hash de senha com scrypt, salt aleatório por senha e comparação em tempo constante (RP-09).
const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;
const SALT_BYTES = 16;

async function hashPassword(plain) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const derived = await scrypt(plain, salt, KEY_LENGTH);
    return `scrypt$${salt.toString('hex')}$${derived.toString('hex')}`;
}

async function verifyPassword(plain, stored) {
    if (typeof plain !== 'string' || typeof stored !== 'string') return false;
    const [scheme, saltHex, hashHex] = stored.split('$');
    if (scheme !== 'scrypt' || !saltHex || !hashHex) return false;
    const expected = Buffer.from(hashHex, 'hex');
    const derived = await scrypt(plain, Buffer.from(saltHex, 'hex'), expected.length);
    return crypto.timingSafeEqual(derived, expected);
}

module.exports = { hashPassword, verifyPassword };
