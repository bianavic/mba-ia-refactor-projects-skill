const { db } = require('../database/connection');

function create(action) {
    return new Promise((resolve, reject) => {
        db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action], (err) => {
            if (err) return reject(err);
            resolve();
        });
    });
}

module.exports = { create };
