const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGatewayService = require('../services/paymentGatewayService');
const cacheService = require('../services/cacheService');

async function checkout(req, res) {
    const { usr: name, eml: email, pwd: rawPassword, c_id: courseId, card: cardNumber } = req.body;

    if (!name || !email || !courseId || !cardNumber) {
        return res.status(400).send('Bad Request');
    }

    let course;
    try {
        course = await courseModel.findActiveById(courseId);
    } catch (err) {
        return res.status(500).send('Erro DB');
    }
    if (!course) return res.status(404).send('Curso não encontrado');

    let existingUser;
    try {
        existingUser = await userModel.findByEmail(email);
    } catch (err) {
        return res.status(500).send('Erro DB');
    }

    let userId;
    if (existingUser) {
        userId = existingUser.id;
    } else {
        try {
            userId = await userModel.create({ name, email, rawPassword });
        } catch (err) {
            return res.status(500).send('Erro ao criar usuário');
        }
    }

    const { status } = paymentGatewayService.charge(cardNumber, course.price);
    if (status === 'DENIED') return res.status(400).send('Pagamento recusado');

    let enrollmentId;
    try {
        enrollmentId = await enrollmentModel.create(userId, courseId);
    } catch (err) {
        return res.status(500).send('Erro Matrícula');
    }

    try {
        await paymentModel.create(enrollmentId, course.price, status);
    } catch (err) {
        return res.status(500).send('Erro Pagamento');
    }

    await auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
    cacheService.set(`last_checkout_${userId}`, course.title);

    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
}

module.exports = { checkout };
