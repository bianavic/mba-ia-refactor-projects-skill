/**
 * O Express 4 não encaminha promise rejeitada de handler async para next(err) —
 * sem este wrapper a requisição simplesmente trava. Todo handler assíncrono
 * registrado em routes/ passa por aqui.
 */
const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = asyncHandler;
