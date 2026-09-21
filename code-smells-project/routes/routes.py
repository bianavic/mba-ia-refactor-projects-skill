from controllers import (
    admin_controller,
    order_controller,
    product_controller,
    system_controller,
    user_controller,
)
from middlewares.auth import requer_admin


def register_routes(app):
    app.add_url_rule("/", "index", system_controller.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", system_controller.health_check, methods=["GET"])

    app.add_url_rule("/produtos", "listar_produtos", product_controller.listar, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", product_controller.buscar, methods=["GET"])
    app.add_url_rule(
        "/produtos/<int:produto_id>", "buscar_produto", product_controller.buscar_por_id, methods=["GET"]
    )
    app.add_url_rule("/produtos", "criar_produto", product_controller.criar, methods=["POST"])
    app.add_url_rule(
        "/produtos/<int:produto_id>", "atualizar_produto", product_controller.atualizar, methods=["PUT"]
    )
    app.add_url_rule(
        "/produtos/<int:produto_id>", "deletar_produto", product_controller.deletar, methods=["DELETE"]
    )

    app.add_url_rule("/usuarios", "listar_usuarios", user_controller.listar, methods=["GET"])
    app.add_url_rule(
        "/usuarios/<int:usuario_id>", "buscar_usuario", user_controller.buscar_por_id, methods=["GET"]
    )
    app.add_url_rule("/usuarios", "criar_usuario", user_controller.criar, methods=["POST"])
    app.add_url_rule("/login", "login", user_controller.login, methods=["POST"])

    app.add_url_rule("/pedidos", "criar_pedido", order_controller.criar, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", order_controller.listar_todos, methods=["GET"])
    app.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_pedidos_usuario",
        order_controller.listar_por_usuario,
        methods=["GET"],
    )
    app.add_url_rule(
        "/pedidos/<int:pedido_id>/status",
        "atualizar_status_pedido",
        order_controller.atualizar_status,
        methods=["PUT"],
    )

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", order_controller.relatorio_vendas, methods=["GET"])

    app.add_url_rule(
        "/admin/reset-db", "reset_database", requer_admin(admin_controller.reset_database), methods=["POST"]
    )
    app.add_url_rule(
        "/admin/query", "executar_query", requer_admin(admin_controller.executar_query), methods=["POST"]
    )
