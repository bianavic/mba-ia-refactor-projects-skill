const reportService = require('../services/reportService');
const { constants } = require('../config');
const { ValidationError } = require('../errors/AppError');

// limit/offset são opcionais; sem eles o relatório completo é devolvido como antes.
function parseIntParam(raw, { min, max }) {
    if (raw === undefined) return undefined;
    if (typeof raw !== 'string' || !/^\d+$/.test(raw)) throw new ValidationError();
    const value = Number(raw);
    if (value < min || (max !== undefined && value > max)) throw new ValidationError();
    return value;
}

async function financialReport(req, res) {
    const limit = parseIntParam(req.query.limit, { min: 1, max: constants.report.maxLimit });
    const offset = parseIntParam(req.query.offset, { min: 0 });
    if (offset !== undefined && limit === undefined) throw new ValidationError();
    res.json(await reportService.financialReport({ limit, offset }));
}

module.exports = { financialReport };
