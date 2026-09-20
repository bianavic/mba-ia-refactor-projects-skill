require('dotenv').config();

const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

const config = {
    serviceName: process.env.SERVICE_NAME || 'ecommerce-api-legacy',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: Number(process.env.PORT) || 3000,
    logLevel: process.env.LOG_LEVEL || 'info',
    defaultPageSize: Number(process.env.DEFAULT_PAGE_SIZE) || DEFAULT_PAGE_SIZE,
    maxPageSize: Number(process.env.MAX_PAGE_SIZE) || MAX_PAGE_SIZE,
    adminToken: process.env.ADMIN_TOKEN,
};

module.exports = config;
