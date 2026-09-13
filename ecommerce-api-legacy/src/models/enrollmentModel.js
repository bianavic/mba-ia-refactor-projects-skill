const { db } = require('../database/connection');

function create(userId, courseId) {
    return new Promise((resolve, reject) => {
        db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId], function (err) {
            if (err) return reject(err);
            resolve(this.lastID);
        });
    });
}

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

    return new Promise((resolve, reject) => {
        db.all(sql, courseIds, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

module.exports = { create, findDetailsByCourseIds };
