const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');
const asyncHandler = require('../middlewares/asyncHandler');
const { validateCheckout, validateReportQuery, validateUserId } = require('../middlewares/validators');

const router = express.Router();

router.post('/api/checkout', validateCheckout, asyncHandler(checkoutController.checkout));
router.get('/api/admin/financial-report', validateReportQuery, asyncHandler(reportController.financialReport));
router.delete('/api/users/:id', validateUserId, asyncHandler(userController.deleteUser));

module.exports = router;
