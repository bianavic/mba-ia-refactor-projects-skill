"""Mascaramento de dados pessoais."""


def mascarar_email(email):
    if not email or "@" not in email:
        return "***"
    local, dominio = email.split("@", 1)
    return (local[:1] or "*") + "***@" + dominio
