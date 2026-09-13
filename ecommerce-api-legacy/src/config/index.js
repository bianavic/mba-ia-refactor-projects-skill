require('dotenv').config();

const config = {
    dbUser: process.env.DB_USER,
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER,
    port: Number(process.env.PORT) || 3000,
    logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = config;
