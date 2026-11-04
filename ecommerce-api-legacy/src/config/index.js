// Único módulo que lê o ambiente. Segredos nunca têm valor literal aqui (RP-02).
const crypto = require('crypto');

function intFromEnv(name, fallback) {
    const raw = process.env[name];
    if (raw === undefined || raw === '') return fallback;
    const value = Number(raw);
    if (!Number.isInteger(value)) throw new Error(`${name} must be an integer`);
    return value;
}

const config = {
    port: intFromEnv('PORT', 3000),
    logLevel: process.env.LOG_LEVEL || 'info',
    db: {
        filename: process.env.DB_FILE || ':memory:',
    },
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    adminToken: process.env.ADMIN_TOKEN || '',
    // Sem SEED_USER_PASSWORD, o usuário semente recebe uma senha aleatória que nunca é exibida.
    seedUserPassword: process.env.SEED_USER_PASSWORD || crypto.randomBytes(24).toString('hex'),
};

const constants = {
    paymentStatus: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
    // Gateway simulado: cartões que começam com este prefixo são aprovados.
    approvedCardPrefix: '4',
    courseActive: 1,
    report: Object.freeze({ maxLimit: 100 }),
    unknownStudentName: 'Unknown',
    removedUserTag: '[removed]',
};

module.exports = { config, constants };
