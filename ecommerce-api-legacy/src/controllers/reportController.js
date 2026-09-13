const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');

const DEFAULT_PAGE_SIZE = 20;

async function financialReport(req, res) {
    const page = Math.max(Number(req.query.page) || 1, 1);
    const perPage = Math.max(Number(req.query.per_page) || DEFAULT_PAGE_SIZE, 1);
    const offset = (page - 1) * perPage;

    let courses;
    try {
        courses = await courseModel.findPage({ limit: perPage, offset });
    } catch (err) {
        return res.status(500).send('Erro DB');
    }

    if (courses.length === 0) return res.json([]);

    const courseIds = courses.map((c) => c.id);
    let enrollmentRows;
    try {
        enrollmentRows = await enrollmentModel.findDetailsByCourseIds(courseIds);
    } catch (err) {
        return res.status(500).send('Erro DB');
    }

    const rowsByCourse = new Map();
    for (const row of enrollmentRows) {
        if (!rowsByCourse.has(row.course_id)) rowsByCourse.set(row.course_id, []);
        rowsByCourse.get(row.course_id).push(row);
    }

    const report = courses.map((course) => {
        const rows = rowsByCourse.get(course.id) || [];
        const revenue = rows.reduce((sum, r) => (r.payment_status === 'PAID' ? sum + r.paid_amount : sum), 0);
        const students = rows.map((r) => ({
            student: r.student_name || 'Unknown',
            paid: r.paid_amount || 0,
        }));

        return { course: course.title, revenue, students };
    });

    res.json(report);
}

module.exports = { financialReport };
