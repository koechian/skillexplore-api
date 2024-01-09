from flask import Flask
from flask_cors import CORS

from .main import main


def create_app():
    app = Flask("__name__")
    app.register_blueprint(main)
    CORS(app, resources={r"/*": {"origins": "*"}})

    return app
