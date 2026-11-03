const db = require('../database/connection');
const { hashPassword, verifyPassword } = require('../utils/password');

// Campos públicos de um usuário: nunca o hash da senha.
const PUBLIC_FIELDS = 'id, name, email';

function findByEmail(email) {
    return db.get('SELECT id, pass FROM users WHERE email = ?', [email]);
}

function findPublicById(id) {
    return db.get(`SELECT ${PUBLIC_FIELDS} FROM users WHERE id = ?`, [id]);
}

async function create({ name, email, password }) {
    const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, await hashPassword(password)]);
    return lastID;
}

function passwordMatches(user, password) {
    return verifyPassword(password, user.pass);
}

async function deleteById(id) {
    const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
    return changes;
}

module.exports = { findByEmail, findPublicById, create, passwordMatches, deleteById };
