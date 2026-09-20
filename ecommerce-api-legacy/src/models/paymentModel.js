const { run } = require('../database/connection');

async function create(enrollmentId, amount, status) {
    const { lastID } = await run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return lastID;
}

module.exports = { create };
