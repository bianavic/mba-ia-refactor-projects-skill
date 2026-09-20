const checkoutService = require('../services/checkoutService');

async function checkout(req, res) {
    const result = await checkoutService.checkout(req.checkout);
    res.status(200).json(result);
}

module.exports = { checkout };
