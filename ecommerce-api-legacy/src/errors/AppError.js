/**
 * Erro de aplicação com status HTTP e mensagem já no formato que a API responde.
 * Serviços/controllers lançam AppError; quem traduz para a resposta é o
 * errorHandler (RP-11) — nenhuma camada abaixo dele toca em `res`.
 */
class AppError extends Error {
    constructor(status, message, cause) {
        super(message);
        this.name = 'AppError';
        this.status = status;
        this.cause = cause;
    }
}

/**
 * Adaptador para `.catch(...)`: converte qualquer falha de infraestrutura em um
 * AppError com a mensagem que aquele passo já respondia antes da refatoração.
 * Substitui os try/catch repetidos em cada chamada de model.
 */
const failWith = (status, message) => (cause) => {
    throw new AppError(status, message, cause);
};

module.exports = { AppError, failWith };
