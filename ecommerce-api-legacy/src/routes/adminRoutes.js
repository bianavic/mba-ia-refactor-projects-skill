const express = require('express');
const reportController = require('../controllers/reportController');
const { requireAdmin } = require('../middleware/requireAdmin');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();
router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));

module.exports = router;
