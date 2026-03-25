from flask import Flask
from .config import config_map
from .extensions import db, migrate, jwt, mail, cors, limiter, sess, init_redis


def create_app(env: str = "production") -> Flask:
    app = Flask(__name__)

    # --- Konfiguracja ---
    app.config.from_object(config_map.get(env, config_map["default"]))

    # --- Rozszerzenia ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
                  supports_credentials=True)
    limiter.init_app(app)
    sess.init_app(app)
    init_redis(app)

    # --- Rejestracja blueprintów ---
    from .routes.auth         import auth_bp
    from .routes.transactions import transactions_bp
    from .routes.events       import events_bp
    from .routes.groups       import groups_bp
    from .routes.invoices     import invoices_bp
    from .routes.admin        import admin_bp

    app.register_blueprint(auth_bp,         url_prefix="/api/auth")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(events_bp,       url_prefix="/api/events")
    app.register_blueprint(groups_bp,       url_prefix="/api/groups")
    app.register_blueprint(invoices_bp,     url_prefix="/api/invoices")
    app.register_blueprint(admin_bp,        url_prefix="/api/admin")

    # --- Health check ---
    @app.get("/api/health")
    def health():
        return {"status": "ok", "env": env}

    # --- Shell context (flask shell) ---
    @app.shell_context_processor
    def make_shell_context():
        from .models.user        import User
        from .models.transaction import Transaction
        from .models.category    import Category
        from .models.event       import Event
        from .models.group       import Group
        return {"db": db, "User": User, "Transaction": Transaction,
                "Category": Category, "Event": Event, "Group": Group}

    return app
