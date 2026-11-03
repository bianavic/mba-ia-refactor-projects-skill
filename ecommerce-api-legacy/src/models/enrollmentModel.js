const db = require('../database/connection');

async function create(userId, courseId) {
    const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return lastID;
}

// Vendas dos cursos informados em uma só consulta (corrige o N+1): matrícula, nome do aluno e pagamento.
function listSalesByCourseIds(courseIds) {
    if (courseIds.length === 0) return Promise.resolve([]);
    const marks = courseIds.map(() => '?').join(',');
    return db.all(
        `SELECT e.id AS enrollment_id, e.course_id, u.name AS student_name,
                p.amount AS amount, p.status AS status
           FROM enrollments e
           LEFT JOIN users u ON u.id = e.user_id
           LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
          WHERE e.course_id IN (${marks})
          ORDER BY e.id`,
        courseIds,
    );
}

function findByUserId(userId) {
    return db.all('SELECT id, course_id FROM enrollments WHERE user_id = ? ORDER BY id', [userId]);
}

// Desvincula o titular sem apagar a matrícula (mantida para a contabilidade).
async function unlinkUser(userId) {
    const { changes } = await db.run('UPDATE enrollments SET user_id = NULL WHERE user_id = ?', [userId]);
    return changes;
}

module.exports = { create, listSalesByCourseIds, findByUserId, unlinkUser };
