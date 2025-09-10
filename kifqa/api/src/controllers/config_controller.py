# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import jsonify, request
from src.services.registry_service import set_model
from src.services.config_service import (
    config as config_service)

def config():
    data = request.get_json()
    model_provider = data.get('model_provider')
    if not model_provider:
        raise ValueError("Missing `model_provider` paramter. Choose among `ibm`, `openai`, and `ollama`")
    model_provider = str(model_provider).lower()
    model_name = data.get('model_name')
    if not model_name:
        raise ValueError("Missing model name")
    api_key = data.get('api_key')
    if not api_key:
        raise ValueError("Missing model api key")
    provider_endpoint = data.get('provider_endpoint')
    if not provider_endpoint:
        raise ValueError("Missing provider endpoint")
    model_params = data.get("model_params")

    try:
        model = config_service(model_name, model_provider, api_key, provider_endpoint,  model_params)
        set_model(model)
        return jsonify({"message": "KIF-QA successfully configured"})
    except Exception as e:
        raise RuntimeError(f"Could not start KIF-QA: {type(e).__name__}: {e}")
