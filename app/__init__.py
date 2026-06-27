"""
app/__init__.py — Flask application factory.

Usage:
    from app import create_app
    flask_app = create_app()
"""
import os

from flask import Flask

from app.config import MAX_UPLOAD_BYTES, RESOURCE_DIR, SECRET_KEY, UPLOAD_FOLDER


def create_app() -> Flask:
    """Create and configure the Flask application."""
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(RESOURCE_DIR, "templates"),
        static_folder=os.path.join(RESOURCE_DIR, "static"),
    )
    flask_app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
    flask_app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    flask_app.config["SECRET_KEY"]         = SECRET_KEY

    # Register blueprints
    from app.routes import history, pages, patients, reports, search, settings
    for bp in (pages.bp, settings.bp, patients.bp, history.bp, reports.bp, search.bp):
        flask_app.register_blueprint(bp)

    return flask_app
