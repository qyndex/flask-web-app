"""Flask web application factory."""
from flask import Flask, render_template

from .extensions import csrf, db, login_manager, ma, migrate
from .auth.routes import auth_bp
from .main.routes import main_bp
from .api.routes import api_bp


def create_app(config_object: str = "config.DevelopmentConfig") -> Flask:
    """Create and configure the Flask web application.

    Args:
        config_object: Dotted-path to a config class.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialise extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Exempt the JSON API from CSRF (tokens sent via headers instead)
    csrf.exempt(api_bp)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
