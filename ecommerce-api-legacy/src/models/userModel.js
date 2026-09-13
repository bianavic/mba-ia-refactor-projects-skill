const { db } = require('../database/connection');
const { hashPassword } = require('../utils/crypto');

const FALLBACK_PASSWORD = '123456';

function findByEmail(email) {
    return new Promise((resolve, reject) => {
        db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
            if (err) return reject(err);
            resolve(user);
        });
    });
}

function create({ name, email, rawPassword }) {
    const hash = hashPassword(rawPassword || FALLBACK_PASSWORD);

    return new Promise((resolve, reject) => {
        db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash], function (err) {
            if (err) return reject(err);
            resolve(this.lastID);
        });
    });
}

function deleteCascade(userId) {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run(
                `DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)`,
                [userId]
            );
            db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
            db.run('DELETE FROM users WHERE id = ?', [userId], (err) => {
                if (err) return reject(err);
                resolve();
            });
        });
    });
}

module.exports = { findByEmail, create, deleteCascade };
