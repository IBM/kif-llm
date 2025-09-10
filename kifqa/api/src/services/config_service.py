# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from kifqa.utils import build_model
from langchain_core.language_models import BaseChatModel


def config(model_name, model_provider, api_key, provider_endpoint, model_params) -> BaseChatModel:
    model_params['temperature'] = 0.7
    model = build_model(model_name, model_provider, provider_endpoint, api_key, **model_params)

    return model
