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

// Mesma conta (ou ausência dela) vista fora e dentro da transação?
const sameAccount = (before, now) => (before?.id ?? null) === (now?.id ?? null) && (before?.pass ?? null) === (now?.pass ?? null);
const MAX_ATTEMPTS = 3;

async function checkout({ name, email, password, courseId, card }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
        // Trabalho lento (scrypt) fora da transação, para não bloquear os demais checkouts e exclusões.
        const existing = await userModel.findByEmail(email);
        if (existing && !(await userModel.passwordMatches(existing, password))) throw new UnauthorizedError();
        const passwordHash = existing ? null : await userModel.hashForStorage(password);

        // Dentro da transação (serializada), só consultas rápidas. Se a conta mudou desde a
        // checagem (ex.: checkout simultâneo do mesmo e-mail novo), refaz a checagem.
        const result = await db.transaction(async () => {
            const current = await userModel.findByEmail(email);
            if (!sameAccount(existing, current)) return null;

            const status = paymentGateway.charge({ card, amount: course.price });
            if (status !== constants.paymentStatus.PAID) throw new PaymentDeclinedError();

            const userId = current ? current.id : await userModel.create({ name, email, passwordHash });
            const enrollmentId = await enrollmentModel.create(userId, course.id);
            await paymentModel.create(enrollmentId, course.price, status);
            await auditLogModel.recordCheckout(course.id, userId);
            return { enrollmentId };
        });
        if (result) return result;
    }
    throw new Error('checkout: conta alterada concorrentemente em todas as tentativas');
}

module.exports = { checkout };
