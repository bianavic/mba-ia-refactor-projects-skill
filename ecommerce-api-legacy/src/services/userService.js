// Direitos do titular: exclusão (desvincula matrículas, mantém pagamentos, anonimiza auditoria) e exportação.
const db = require('../database/connection');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const { NotFoundError } = require('../errors/AppError');

const USER_NOT_FOUND = 'Usuário não encontrado';

function deleteUser(id) {
    return db.transaction(async () => {
        const user = await userModel.findPublicById(id);
        if (!user) throw new NotFoundError(USER_NOT_FOUND);
        await enrollmentModel.unlinkUser(id);
        await auditLogModel.redactUser(id);
        await userModel.deleteById(id);
    });
}

async function exportUser(id) {
    const user = await userModel.findPublicById(id);
    if (!user) throw new NotFoundError(USER_NOT_FOUND);
    const enrollments = await enrollmentModel.findByUserId(id);
    const payments = await paymentModel.findByEnrollmentIds(enrollments.map((e) => e.id));
    return { user, enrollments, payments };
}

module.exports = { deleteUser, exportUser };
