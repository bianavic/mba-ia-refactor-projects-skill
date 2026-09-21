const { get, all } = require('../database/connection');

function findActiveById(id) {
    return get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

function findPage({ limit, offset }) {
    return all('SELECT * FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset]);
}

module.exports = { findActiveById, findPage };
