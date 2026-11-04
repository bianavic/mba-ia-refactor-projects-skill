// Gateway de pagamento simulado (sistema externo). Loga apenas o resultado e o cartão mascarado.
const { config, constants } = require('../config');
const { logger } = require('../utils/logger');

function maskCard(card) {
    return `****${card.slice(-4)}`;
}

// config.paymentGatewayKey seria usada por um gateway real; nunca é logada nem devolvida.
function charge({ card, amount }) {
    const { PAID, DENIED } = constants.paymentStatus;
    const status = card.startsWith(constants.approvedCardPrefix) ? PAID : DENIED;
    logger.info(`Pagamento ${status} de ${amount} no cartão ${maskCard(card)}${config.paymentGatewayKey ? '' : ' (gateway sem chave configurada)'}`);
    return status;
}

module.exports = { charge, maskCard };
