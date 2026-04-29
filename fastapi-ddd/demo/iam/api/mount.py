from demo.iam.api.auth import router


def router_register_to(app):
    app.include_router(router)
