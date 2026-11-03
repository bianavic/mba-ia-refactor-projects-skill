const { AppError } = require('./AppError');
const { logger } = require('../utils/logger');

// Registrado por último no app.js; precisa manter 4 argumentos.
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.status).send(err.message);
    // JSON malformado ou corpo inválido vindos do express.json()
    if (err.type === 'entity.parse.failed' || err.status === 400) return res.status(400).send('Bad Request');
    if (err.status === 413) return res.status(413).send('Payload Too Large');
    logger.error(`Erro não tratado em ${req.method} ${req.path}: ${err.stack || err.message}`);
    return res.status(500).send('Erro DB');
}

module.exports = { errorHandler };
