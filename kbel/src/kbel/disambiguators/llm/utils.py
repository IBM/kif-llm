# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel


def build_model(
    model_name: str,
    provider: Literal['ibm', 'openai', 'ollama'],
    endpoint: str,
    apikey: str,
    **kwargs) -> BaseChatModel:
    endpoint = endpoint
    apikey = apikey
    assert endpoint and apikey

    if provider == 'ibm':
        if project_id:=kwargs.get('project_id'):
            kwargs.__delitem__('project_id')
            from langchain_ibm import ChatWatsonx
            return ChatWatsonx(
                model_id=model_name,
                apikey=apikey, # type: ignore
                url=endpoint, # type: ignore
                project_id=project_id,
                params=kwargs
            )
        raise ValueError(f'Project ID not found while initializing IBM models.')
    elif provider == 'openai':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=apikey, # type: ignore
            base_url=endpoint, # type: ignore
            params=kwargs)

    raise ValueError(f'Could not initialize `{provider}` not exist.')
