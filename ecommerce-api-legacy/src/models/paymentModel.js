const db = require('../database/connection');

async function create(enrollmentId, amount, status) {
    const { lastID } = await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]);
    return lastID;
}

function findByEnrollmentIds(enrollmentIds) {
    if (enrollmentIds.length === 0) return Promise.resolve([]);
    const marks = enrollmentIds.map(() => '?').join(',');
    return db.all(`SELECT id, enrollment_id, amount, status FROM payments WHERE enrollment_id IN (${marks}) ORDER BY id`,
        enrollmentIds);
}

module.exports = { create, findByEnrollmentIds };
