const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database(':memory:');

/**
 * Wrappers com Promise em cima do driver de callback. Existem para que nenhum
 * erro possa ser engolido por falta de callback — era assim que o cascade de
 * usuário reportava sucesso sem ter apagado nada.
 */
function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

/**
 * Executa `work` dentro de uma transação. Qualquer exceção desfaz tudo que foi
 * escrito ali dentro — é o que impede uma matrícula sem pagamento (ou o
 * contrário) depois que o cartão já foi cobrado.
 */
async function withTransaction(work) {
    await run('BEGIN');
    try {
        const result = await work();
        await run('COMMIT');
        return result;
    } catch (err) {
        await run('ROLLBACK').catch(() => {});
        throw err;
    }
}

async function initSchema() {
    await run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

    await run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
    await run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    await run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { db, run, get, all, withTransaction, initSchema };
