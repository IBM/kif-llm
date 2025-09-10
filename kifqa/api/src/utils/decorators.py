# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from functools import wraps
from flask import jsonify
from src.services.registry_service import get_model

def require_qa(func):
    """Decorator that ensures the KIFQA object is already configured for the user."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        qa = get_model()
        if qa is None:
            return jsonify({"error": "KIFQA not configured for this user"}), 400
        return func(qa, *args, **kwargs)
    return wrapper
