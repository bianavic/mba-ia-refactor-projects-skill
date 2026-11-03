// Conexão única aberta pela raiz de composição; expõe run/get/all em Promise e transações serializadas.
const sqlite3 = require('sqlite3');

let handle = null;
let queue = Promise.resolve();

function open(filename) {
    return new Promise((resolve, reject) => {
        const db = new sqlite3.Database(filename, (err) => {
            if (err) return reject(err);
            handle = db;
            resolve();
        });
    });
}

function current() {
    if (!handle) throw new Error('Database not opened');
    return handle;
}

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        current().run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        current().get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        current().all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

// Uma transação por vez na conexão compartilhada: BEGIN/COMMIT ou ROLLBACK em caso de erro.
function transaction(work) {
    const result = queue.then(async () => {
        await run('BEGIN IMMEDIATE');
        try {
            const value = await work();
            await run('COMMIT');
            return value;
        } catch (err) {
            await run('ROLLBACK');
            throw err;
        }
    });
    queue = result.catch(() => {});
    return result;
}

function close() {
    return new Promise((resolve) => {
        if (!handle) return resolve();
        handle.close(() => resolve());
        handle = null;
    });
}

module.exports = { open, run, get, all, transaction, close };
