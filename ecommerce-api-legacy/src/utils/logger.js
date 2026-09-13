const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const currentLevel = LEVELS[config.logLevel] ?? LEVELS.info;

function write(level, message, meta) {
    if (LEVELS[level] > currentLevel) return;

    const entry = { timestamp: new Date().toISOString(), level, message, ...meta };
    const line = JSON.stringify(entry);
    level === 'error' ? console.error(line) : console.log(line);
}

module.exports = {
    error: (message, meta) => write('error', message, meta),
    warn: (message, meta) => write('warn', message, meta),
    info: (message, meta) => write('info', message, meta),
    debug: (message, meta) => write('debug', message, meta),
};
