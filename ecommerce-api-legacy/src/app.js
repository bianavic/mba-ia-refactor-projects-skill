// Raiz de composição: configuração, banco, middlewares, rotas e tratamento de erros.
const express = require('express');
const { config } = require('./config');
const db = require('./database/connection');
const { initDatabase } = require('./database/schema');
const { logger } = require('./utils/logger');
const { errorHandler } = require('./errors/errorHandler');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');

async function start() {
    await db.open(config.db.filename);
    await initDatabase(config.seedUserPassword);
    if (!config.adminToken) logger.warn('ADMIN_TOKEN não configurado: rotas administrativas responderão 401');

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes);
    app.use(adminRoutes);
    app.use(userRoutes);
    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

start().catch((err) => {
    logger.error(`Falha ao iniciar: ${err.stack || err.message}`);
    process.exit(1);
});
