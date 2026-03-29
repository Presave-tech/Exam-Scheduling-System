"""
Flask application factory.
Initializes the app, database, and registers blueprints.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (shared instance used by models)
db = SQLAlchemy()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Load configuration from config.py
    app.config.from_object("config.Config")

    # Ensure the instance folder exists (holds SQLite DB)
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance"), exist_ok=True)

    # Bind SQLAlchemy to the app
    db.init_app(app)

    # Register routes blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Create all database tables on first run
    with app.app_context():
        db.create_all()

    return app
