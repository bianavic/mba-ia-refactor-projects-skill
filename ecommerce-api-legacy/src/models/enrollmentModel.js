const { run, all } = require('../database/connection');

async function create(userId, courseId) {
    const { lastID } = await run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return lastID;
}

/** Uma única query com IN (...) no lugar de um SELECT por curso (AP-08). */
function findDetailsByCourseIds(courseIds) {
    if (courseIds.length === 0) return Promise.resolve([]);

    const placeholders = courseIds.map(() => '?').join(',');
    const sql = `
        SELECT e.id AS enrollment_id, e.course_id, u.name AS student_name,
               p.amount AS paid_amount, p.status AS payment_status
        FROM enrollments e
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        WHERE e.course_id IN (${placeholders})
    `;

    return all(sql, courseIds);
}

module.exports = { create, findDetailsByCourseIds };
