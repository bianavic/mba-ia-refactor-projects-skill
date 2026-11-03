// Esquema e dados semente carregados no boot. A senha semente vem da configuração e é gravada com hash.
const db = require('./connection');
const { hashPassword } = require('../utils/password');
const { constants } = require('../config');

async function createSchema() {
    await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    // Um e-mail = uma conta, garantido pelo próprio banco.
    await db.run('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)');
    await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

// Só semeia um banco vazio, para que um arquivo reaproveitado não duplique linhas.
async function seed(seedUserPassword) {
    const existing = await db.get('SELECT COUNT(*) AS total FROM users');
    if (existing.total > 0) return;
    const { PAID } = constants.paymentStatus;
    const active = constants.courseActive;
    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', await hashPassword(seedUserPassword)]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
            ['Clean Architecture', 997.0, active, 'Docker', 497.0, active]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [1, 997.0, PAID]);
    });
}

async function initDatabase(seedUserPassword) {
    await createSchema();
    await seed(seedUserPassword);
}

module.exports = { initDatabase };
