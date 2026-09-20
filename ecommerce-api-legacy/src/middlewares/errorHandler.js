const logger = require('../utils/logger');
const { AppError } = require('../errors/AppError');

/**
 * Único lugar que traduz erro em resposta HTTP (RP-11).
 * AppError carrega o status e a mensagem que a API já respondia antes da
 * refatoração — o formato das respostas de erro é contrato e não mudou.
 */
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
    if (err instanceof AppError) {
        const meta = { status: err.status, path: req.path, cause: err.cause && err.cause.message };
        if (err.status >= 500) {
            logger.error(err.message, meta);
        } else {
            logger.warn(err.message, meta);
        }
        return res.status(err.status).send(err.message);
    }

    // Body JSON malformado: o express.json() lança antes de qualquer validação.
    if (err.type === 'entity.parse.failed') {
        logger.warn('Malformed JSON body', { path: req.path });
        return res.status(400).send('Bad Request');
    }

    logger.error('Unhandled error', { message: err.message, path: req.path });
    res.status(500).json({ error: 'internal_error' });
}

module.exports = errorHandler;
