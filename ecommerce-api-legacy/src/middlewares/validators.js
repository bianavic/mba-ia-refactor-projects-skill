const config = require('../config');
const { AppError } = require('../errors/AppError');

// Mesma mensagem que a API já respondia para requisição malformada.
const BAD_REQUEST = 'Bad Request';

const CARD_NUMBER = /^\d{12,19}$/;

function isPositiveInt(value) {
    return /^\d+$/.test(String(value).trim()) && Number(value) > 0;
}

function reject() {
    throw new AppError(400, BAD_REQUEST);
}

/**
 * POST /api/checkout — os nomes abreviados (usr, eml, pwd, c_id, card) são
 * contrato da API e ficam como estão (RP-15); a tradução para nomes
 * descritivos acontece aqui, uma vez, e o service só vê o objeto validado.
 */
function validateCheckout(req, res, next) {
    const { usr, eml, pwd, c_id: courseId, card } = req.body || {};

    if (!usr || !eml || !pwd || !courseId || !card) reject();
    if (!isPositiveInt(courseId)) reject();
    if (typeof card !== 'string' || !CARD_NUMBER.test(card)) reject();

    req.checkout = {
        name: String(usr),
        email: String(eml),
        rawPassword: String(pwd),
        courseId: Number(courseId),
        cardNumber: card,
    };
    next();
}

/** GET /api/admin/financial-report — page/per_page numéricos e per_page limitado. */
function validateReportQuery(req, res, next) {
    const { page, per_page: perPage } = req.query;

    if (page !== undefined && !isPositiveInt(page)) reject();
    if (perPage !== undefined && !isPositiveInt(perPage)) reject();

    req.pagination = {
        page: Number(page) || 1,
        perPage: Math.min(Number(perPage) || config.defaultPageSize, config.maxPageSize),
    };
    next();
}

/** DELETE /api/users/:id */
function validateUserId(req, res, next) {
    if (!isPositiveInt(req.params.id)) reject();

    req.userId = Number(req.params.id);
    next();
}

module.exports = { validateCheckout, validateReportQuery, validateUserId };
