"""Fluxo HTTP de produtos: validação e forma da resposta."""
import logging

from config import settings
from errors.exceptions import NotFound, ValidationError
from models import produto_model

logger = logging.getLogger(__name__)


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_produto(dados):
    """Validador único de criação e atualização."""
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", settings.CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _numero(preco):
        raise ValidationError("Preço deve ser um número")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser um número inteiro")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria deve ser texto")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < settings.NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > settings.NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in settings.CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(settings.CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def listar_produtos(paginacao):
    produtos = produto_model.listar(paginacao)
    logger.info("Listando %s produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def obter_produto(id):
    produto = produto_model.obter_por_id(id)
    if not produto:
        raise NotFound("Produto não encontrado", incluir_sucesso=True)
    return {"dados": produto, "sucesso": True}, 200


def criar_produto(dados):
    p = _validar_produto(dados)
    id = produto_model.criar(p["nome"], p["descricao"], p["preco"], p["estoque"], p["categoria"])
    logger.info("Produto criado com ID: %s", id)
    return {"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar_produto(id, dados):
    if not produto_model.obter_por_id(id):
        raise NotFound("Produto não encontrado")
    p = _validar_produto(dados)
    produto_model.atualizar(id, p["nome"], p["descricao"], p["preco"], p["estoque"], p["categoria"])
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar_produto(id):
    if not produto_model.obter_por_id(id):
        raise NotFound("Produto não encontrado")
    produto_model.deletar(id)
    logger.info("Produto %s deletado", id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def _preco_filtro(valor, nome):
    if not valor:
        return valor
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome + " deve ser numérico")


def buscar_produtos(args, paginacao):
    termo = args.get("q", "")
    categoria = args.get("categoria", None)
    preco_min = _preco_filtro(args.get("preco_min", None), "preco_min")
    preco_max = _preco_filtro(args.get("preco_max", None), "preco_max")
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max, paginacao)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
