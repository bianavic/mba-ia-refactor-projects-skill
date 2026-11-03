"""Erros tipados; o handler central os converte em respostas."""


class AppError(Exception):
    status = 500

    def __init__(self, mensagem, incluir_sucesso=False, status=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.incluir_sucesso = incluir_sucesso
        if status is not None:
            self.status = status

    def corpo(self):
        corpo = {"erro": self.mensagem}
        if self.incluir_sucesso:
            corpo["sucesso"] = False
        return corpo


class ValidationError(AppError):
    status = 400


class NotFound(AppError):
    status = 404


class Unauthorized(AppError):
    status = 401


class Forbidden(AppError):
    status = 403
