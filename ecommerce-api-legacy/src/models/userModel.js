const { run, get, withTransaction } = require('../database/connection');
const { hashPassword } = require('../utils/crypto');

function findByEmail(email) {
    return get('SELECT id FROM users WHERE email = ?', [email]);
}

async function create({ name, email, rawPassword }) {
    const hash = hashPassword(rawPassword);
    const { lastID } = await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash]);
    return lastID;
}

/**
 * Remove o usuário e tudo que depende dele. Transacional: ou some pagamento,
 * matrícula e usuário juntos, ou nada sai. Retorna quantas linhas de `users`
 * foram afetadas para que o chamador distinga remoção real de id inexistente.
 */
function deleteCascade(userId) {
    return withTransaction(async () => {
        await run(
            'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
            [userId]
        );
        await run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        const { changes } = await run('DELETE FROM users WHERE id = ?', [userId]);
        return { changes };
    });
}

module.exports = { findByEmail, create, deleteCascade };
