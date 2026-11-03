const db = require('../database/connection');
const { constants } = require('../config');

function checkoutAction(courseId, userId) {
    return `Checkout curso ${courseId} por ${userId}`;
}

async function recordCheckout(courseId, userId) {
    await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [checkoutAction(courseId, userId)]);
}

// Troca "por <id>" por "por [removed]" nos registros do titular apagado.
async function redactUser(userId) {
    const suffix = ` por ${userId}`;
    const { changes } = await db.run(
        `UPDATE audit_logs
            SET action = substr(action, 1, length(action) - length(?)) || ?
          WHERE substr(action, -length(?)) = ?`,
        [suffix, ` por ${constants.removedUserTag}`, suffix, suffix],
    );
    return changes;
}

module.exports = { recordCheckout, redactUser };
