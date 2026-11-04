// Valida o corpo do checkout (campos usr/eml/pwd/c_id/card são contrato) e chama o serviço.
const checkoutService = require('../services/checkoutService');
const { ValidationError } = require('../errors/AppError');

const isNonEmptyString = (v) => typeof v === 'string' && v.trim() !== '';
const CARD_PATTERN = /^\d{12,19}$/;

function parseCheckoutBody(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};
    const valid = isNonEmptyString(usr)
        && isNonEmptyString(eml) && eml.includes('@')
        && isNonEmptyString(pwd)
        && Number.isInteger(courseId) && courseId > 0
        && typeof card === 'string' && CARD_PATTERN.test(card);
    if (!valid) throw new ValidationError();
    return { name: usr, email: eml, password: pwd, courseId, card };
}

async function checkout(req, res) {
    const { enrollmentId } = await checkoutService.checkout(parseCheckoutBody(req.body));
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
}

module.exports = { checkout };
