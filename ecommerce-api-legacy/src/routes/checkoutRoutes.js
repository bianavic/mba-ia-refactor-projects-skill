const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();
router.post('/api/checkout', asyncHandler(checkoutController.checkout));

module.exports = router;
