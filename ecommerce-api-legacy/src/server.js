const createApp = require('./app');
const config = require('./config');
const logger = require('./utils/logger');
const { initSchema } = require('./database/connection');

function listen(app) {
    return new Promise((resolve, reject) => {
        const server = app.listen(config.port, () => {
            logger.info(`${config.serviceName} rodando na porta ${config.port}...`);
            resolve(server);
        });
        // listen() reporta falha por evento, não por exceção: sem este handler
        // um EADDRINUSE derruba o processo com stack trace crua.
        server.once('error', reject);
    });
}

async function start() {
    await initSchema();
    await listen(createApp());
}

start().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', { message: err.message, code: err.code });
    process.exit(1);
});
