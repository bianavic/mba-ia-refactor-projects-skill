const config = require('../config');
const { AppError } = require('../errors/AppError');

/**
 * AP-17: guarda mínima para as duas rotas sem checagem de identidade
 * (financial-report, delete de usuário). Sem ADMIN_TOKEN configurado no
 * servidor, as rotas ficam desabilitadas em vez de abertas por padrão —
 * mesma convenção do code-smells-project (middlewares/auth.py).
 */
function requireAdminToken(req, res, next) {
    if (!config.adminToken) {
        throw new AppError(403, 'Endpoints administrativos desabilitados');
    }
    if (req.headers['x-admin-token'] !== config.adminToken) {
        throw new AppError(401, 'Não autorizado');
    }
    next();
}

module.exports = requireAdminToken;
