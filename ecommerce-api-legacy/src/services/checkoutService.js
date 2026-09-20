const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGatewayService = require('./paymentGatewayService');
const { withTransaction } = require('../database/connection');
const { AppError, failWith } = require('../errors/AppError');
const logger = require('../utils/logger');

/**
 * Grava matrícula e pagamento como uma unidade só. O cartão já foi cobrado
 * neste ponto, então uma falha aqui deixa dinheiro cobrado sem contrapartida:
 * a transação desfaz a escrita parcial e o estorno pendente fica registrado no
 * audit_log em vez de sumir.
 */
async function persistEnrollmentAndPayment({ userId, courseId, price, status }) {
    try {
        return await withTransaction(async () => {
            const enrollmentId = await enrollmentModel
                .create(userId, courseId)
                .catch(failWith(500, 'Erro Matrícula'));

            await paymentModel
                .create(enrollmentId, price, status)
                .catch(failWith(500, 'Erro Pagamento'));

            return enrollmentId;
        });
    } catch (err) {
        logger.error('Checkout persistence failed after a successful charge', {
            userId,
            courseId,
            amount: price,
            cause: err.cause ? err.cause.message : err.message,
        });
        await auditLogModel
            .create(`ESTORNO PENDENTE: cobranca de ${price} do usuario ${userId} no curso ${courseId} sem matricula`)
            .catch(() => {});

        throw err instanceof AppError ? err : new AppError(500, 'Erro Matrícula', err);
    }
}

/**
 * Fluxo completo de compra de um curso. Recebe dados já validados pela camada
 * de rota e devolve o corpo da resposta de sucesso — não conhece req/res.
 */
async function checkout({ name, email, rawPassword, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(courseId).catch(failWith(500, 'Erro DB'));
    if (!course) throw new AppError(404, 'Curso não encontrado');

    const existingUser = await userModel.findByEmail(email).catch(failWith(500, 'Erro DB'));
    const userId = existingUser
        ? existingUser.id
        : await userModel.create({ name, email, rawPassword }).catch(failWith(500, 'Erro ao criar usuário'));

    const { status } = paymentGatewayService.charge(cardNumber, course.price);
    if (status === 'DENIED') throw new AppError(400, 'Pagamento recusado');

    const enrollmentId = await persistEnrollmentAndPayment({
        userId,
        courseId,
        price: course.price,
        status,
    });

    // Auditoria é registro paralelo: a compra já se concretizou, uma falha aqui
    // não pode derrubar a resposta do cliente — mas também não pode ser ignorada.
    await auditLogModel.create(`Checkout curso ${courseId} por ${userId}`).catch((err) => {
        logger.error('Audit log write failed', { userId, courseId, cause: err.message });
    });

    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { checkout };
