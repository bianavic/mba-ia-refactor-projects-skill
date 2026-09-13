const { db } = require('../database/connection');

function findActiveById(id) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id], (err, course) => {
            if (err) return reject(err);
            resolve(course);
        });
    });
}

function findPage({ limit, offset }) {
    return new Promise((resolve, reject) => {
        db.all('SELECT * FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset], (err, courses) => {
            if (err) return reject(err);
            resolve(courses);
        });
    });
}

module.exports = { findActiveById, findPage };
