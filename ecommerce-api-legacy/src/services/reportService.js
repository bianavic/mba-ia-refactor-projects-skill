// Relatório financeiro: cursos (paginados ou não) com receita paga e alunos, em duas consultas.
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const { constants } = require('../config');

async function financialReport({ limit, offset } = {}) {
    const courses = await courseModel.list({ limit, offset });
    const sales = await enrollmentModel.listSalesByCourseIds(courses.map((c) => c.id));

    const byCourse = new Map(courses.map((c) => [c.id, { course: c.title, revenue: 0, students: [] }]));
    for (const sale of sales) {
        const entry = byCourse.get(sale.course_id);
        if (sale.status === constants.paymentStatus.PAID) entry.revenue += sale.amount;
        entry.students.push({
            student: sale.student_name ?? constants.unknownStudentName,
            paid: sale.amount ?? 0,
        });
    }
    return [...byCourse.values()];
}

module.exports = { financialReport };
