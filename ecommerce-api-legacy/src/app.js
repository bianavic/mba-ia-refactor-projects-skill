const express = require('express');
const routes = require('./routes');
const notFoundHandler = require('./middlewares/notFoundHandler');
const errorHandler = require('./middlewares/errorHandler');

/**
 * Composition root: monta a aplicação e devolve. Sem efeito colateral — quem
 * abre porta e cria schema é o server.js, para que testes possam importar a
 * app sem subir um servidor.
 */
function createApp() {
    const app = express();

    app.use(express.json());
    app.use(routes);
    app.use(notFoundHandler);
    app.use(errorHandler);

    return app;
}

module.exports = createApp;
