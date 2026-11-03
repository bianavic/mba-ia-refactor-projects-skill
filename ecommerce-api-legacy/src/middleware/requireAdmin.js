// Guarda de administrador: header X-Admin-Token comparado em tempo constante com ADMIN_TOKEN (RP-16).
// Sem ADMIN_TOKEN configurado, toda chamada administrativa responde 401 (falha fechada).
const crypto = require('crypto');
const { config } = require('../config');
const { UnauthorizedError } = require('../errors/AppError');

const digest = (value) => crypto.createHash('sha256').update(value).digest();
const expected = config.adminToken ? digest(config.adminToken) : null;

function requireAdmin(req, res, next) {
    const provided = req.get('X-Admin-Token');
    if (!expected || !provided || !crypto.timingSafeEqual(digest(provided), expected)) {
        return next(new UnauthorizedError());
    }
    return next();
}

module.exports = { requireAdmin };
