// Express 4 não encaminha promessas rejeitadas: este wrapper leva o erro ao handler central.
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

module.exports = { asyncHandler };
