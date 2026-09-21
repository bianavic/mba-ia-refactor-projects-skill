const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdminToken = require('../middlewares/requireAdminToken');
const { validateCheckout, validateReportQuery, validateUserId } = require('../middlewares/validators');

const router = express.Router();

router.post('/api/checkout', validateCheckout, asyncHandler(checkoutController.checkout));
router.get(
    '/api/admin/financial-report',
    requireAdminToken,
    validateReportQuery,
    asyncHandler(reportController.financialReport)
);
router.delete('/api/users/:id', requireAdminToken, validateUserId, asyncHandler(userController.deleteUser));

module.exports = router;
