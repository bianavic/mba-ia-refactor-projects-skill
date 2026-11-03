const express = require('express');
const userController = require('../controllers/userController');
const { requireAdmin } = require('../middleware/requireAdmin');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();
router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.deleteUser));
router.get('/api/users/:id/export', requireAdmin, asyncHandler(userController.exportUser));

module.exports = router;
