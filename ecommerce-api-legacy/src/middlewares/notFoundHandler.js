const logger = require('../utils/logger');

/**
 * Rota não registrada. Sem este middleware a requisição cai no handler final do
 * Express, que responde HTML — quebrando o contrato JSON do errorHandler.
 */
function notFoundHandler(req, res) {
    logger.warn('Route not found', { method: req.method, path: req.path });
    res.status(404).json({ error: 'not_found' });
}

module.exports = notFoundHandler;
