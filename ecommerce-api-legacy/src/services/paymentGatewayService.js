const config = require('../config');
const logger = require('../utils/logger');

const APPROVED_CARD_PREFIX = '4';

function maskCard(cardNumber) {
    return `${cardNumber.slice(0, 4)}${'*'.repeat(Math.max(cardNumber.length - 8, 0))}${cardNumber.slice(-4)}`;
}

function charge(cardNumber, amount) {
    logger.info('Processing payment', { card: maskCard(cardNumber), amount, gateway: config.paymentGatewayKey ? 'configured' : 'missing-key' });

    const status = cardNumber.startsWith(APPROVED_CARD_PREFIX) ? 'PAID' : 'DENIED';
    return { status };
}

module.exports = { charge };
