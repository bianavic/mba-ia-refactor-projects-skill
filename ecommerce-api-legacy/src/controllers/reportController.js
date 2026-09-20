const reportService = require('../services/reportService');

async function financialReport(req, res) {
    const report = await reportService.financialReport(req.pagination);
    res.json(report);
}

module.exports = { financialReport };
