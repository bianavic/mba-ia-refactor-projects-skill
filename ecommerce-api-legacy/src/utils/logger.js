// Logger com níveis. Nunca recebe dados pessoais, senhas, chaves ou cartões completos (RP-17).
const { config } = require('../config');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = LEVELS[config.logLevel] ?? LEVELS.info;

function write(name, stream) {
    return (message) => {
        if (LEVELS[name] < threshold) return;
        stream.write(`${new Date().toISOString()} [${name.toUpperCase()}] ${message}\n`);
    };
}

const logger = {
    debug: write('debug', process.stdout),
    info: write('info', process.stdout),
    warn: write('warn', process.stderr),
    error: write('error', process.stderr),
};

module.exports = { logger };
