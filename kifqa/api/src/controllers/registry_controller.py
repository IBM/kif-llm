# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import jsonify
from src.services.registry_service import  get_model


def model():
    model = get_model()

    if model:
        return jsonify({"model": True})
    else:
        return jsonify({"model": False})
