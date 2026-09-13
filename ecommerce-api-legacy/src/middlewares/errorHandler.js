const logger = require('../utils/logger');

function errorHandler(err, req, res, next) {
    logger.error('Unhandled error', { message: err.message, path: req.path });
    res.status(500).json({ error: 'internal_error' });
}

module.exports = errorHandler;
