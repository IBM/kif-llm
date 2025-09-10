# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from flask.typing import ResponseReturnValue
from src.routes.routes import blueprint


def create_app() -> Flask:
    app = Flask(__name__)

    # Secret key for sessions
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")
    app.config.from_object("config")
    app.config["PROPAGATE_EXCEPTIONS"] = True
    CORS(app, supports_credentials=True)

    # ----------------------
    # Logging setup
    # ----------------------
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    # ----------------------
    # Global error handler
    # ----------------------
    @app.errorhandler(Exception)
    def handle_exception(e: Exception) -> ResponseReturnValue:
        # Log full exception with stack trace
        app.logger.exception("Unhandled exception occurred")

        if isinstance(e, HTTPException):
            return jsonify(error=e.name, details=e.description), e.code

        return jsonify(error="Internal Server Error", details=str(e)), 500


    app.register_blueprint(blueprint)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
