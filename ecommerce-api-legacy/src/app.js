const express = require('express');
const config = require('./config');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const logger = require('./utils/logger');
const { initSchema } = require('./database/connection');

const app = express();
app.use(express.json());

initSchema();

app.use(routes);
app.use(errorHandler);

app.listen(config.port, () => {
    logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
});

module.exports = app;
