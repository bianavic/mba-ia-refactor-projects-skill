// Caso de uso de checkout: curso, usuário, pagamento, matrícula e auditoria numa única transação.
const db = require('../database/connection');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGateway = require('./paymentGatewayService');
const { constants } = require('../config');
const { NotFoundError, UnauthorizedError, PaymentDeclinedError } = require('../errors/AppError');

async function checkout({ name, email, password, courseId, card }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    // Conta existente: só o titular (senha correta) pode comprar em seu nome.
    const existing = await userModel.findByEmail(email);
    if (existing && !(await userModel.passwordMatches(existing, password))) throw new UnauthorizedError();

    const status = paymentGateway.charge({ card, amount: course.price });
    if (status !== constants.paymentStatus.PAID) throw new PaymentDeclinedError();

    return db.transaction(async () => {
        const userId = existing ? existing.id : await userModel.create({ name, email, password });
        const enrollmentId = await enrollmentModel.create(userId, course.id);
        await paymentModel.create(enrollmentId, course.price, status);
        await auditLogModel.recordCheckout(course.id, userId);
        return { enrollmentId };
    });
}

module.exports = { checkout };
