const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const { failWith } = require('../errors/AppError');

const PAID = 'PAID';

/** Receita de um curso: soma apenas os pagamentos efetivamente liquidados. */
function revenueOf(rows) {
    return rows.reduce((sum, row) => (row.payment_status === PAID ? sum + row.paid_amount : sum), 0);
}

function groupByCourse(rows) {
    const byCourse = new Map();
    for (const row of rows) {
        if (!byCourse.has(row.course_id)) byCourse.set(row.course_id, []);
        byCourse.get(row.course_id).push(row);
    }
    return byCourse;
}

async function financialReport({ page, perPage }) {
    const offset = (page - 1) * perPage;

    const courses = await courseModel.findPage({ limit: perPage, offset }).catch(failWith(500, 'Erro DB'));
    if (courses.length === 0) return [];

    const courseIds = courses.map((course) => course.id);
    const enrollmentRows = await enrollmentModel
        .findDetailsByCourseIds(courseIds)
        .catch(failWith(500, 'Erro DB'));

    const rowsByCourse = groupByCourse(enrollmentRows);

    return courses.map((course) => {
        const rows = rowsByCourse.get(course.id) || [];
        return {
            course: course.title,
            revenue: revenueOf(rows),
            students: rows.map((row) => ({
                student: row.student_name || 'Unknown',
                paid: row.paid_amount || 0,
            })),
        };
    });
}

module.exports = { financialReport };
