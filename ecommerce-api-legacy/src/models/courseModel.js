const db = require('../database/connection');
const { constants } = require('../config');

function findActiveById(id) {
    return db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = ?', [id, constants.courseActive]);
}

// Sem limit, devolve todos os cursos (resposta idêntica à original); com limit, pagina por id.
function list({ limit, offset = 0 } = {}) {
    if (limit === undefined) return db.all('SELECT id, title FROM courses ORDER BY id');
    return db.all('SELECT id, title FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset]);
}

module.exports = { findActiveById, list };
