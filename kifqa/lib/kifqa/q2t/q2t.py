# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os
from dataclasses import asdict
from typing import Any, Literal, Optional, Sequence

import nest_asyncio
from langchain.output_parsers import PydanticOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers.base import BaseOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field, RootModel

from kifqa.constants import Q2T_DEFAULT_PROMPT
from kifqa.model.example import Example

nest_asyncio.apply()


class Triple(BaseModel):
    subject: Optional[str] = Field(None)
    property: Optional[str] = Field(None)
    object: Optional[str] = Field(None)


class Triples(Triple):
    constraints: Optional[list[Triple]] = Field(default_factory=list)


class LLM_Response(RootModel[list[Triples]]):
    pass


class QuestionToTriples:
    question: str
    system_prompt: str
    parser: BaseOutputParser
    few_shots: Optional[list[Example] | str] = None

    _model: BaseChatModel

    def __init__(self,
                 model_name: Optional[str] = None,
                 model_provider: Optional[Literal['ibm', 'openai', 'ollama']] = None,
                 model_params: Optional[Any] = None,
                 model: Optional[BaseChatModel] = None,
                 system_prompt: Optional[str] = None,
                 parser: Optional[BaseOutputParser] = None) -> None:

        self.system_prompt = system_prompt if system_prompt else Q2T_DEFAULT_PROMPT
        assert self._is_valid_system_prompt(
        ), 'Please, provide a valid system prompt.'

        self.parser = parser if parser else PydanticOutputParser(
            pydantic_object=LLM_Response)

        if model:
            self._model = model
        elif model_name and model_provider:
            self._model = self.build_model(
                model_name= model_name, provider=model_provider, model_params=model_params)
        else:
            raise ValueError('LLM Model not initialized.')

    def _is_valid_system_prompt(self):
        # TODO: create rules to validate prompt
        if self.system_prompt:
            return True
        return False

    @property
    def model(self) -> BaseChatModel:
        return self._model

    @model.setter
    def model(self, value: BaseChatModel) -> None:
        self._model = value

    def build_model(self,
                    model_name: str,
                    provider: Literal['ibm', 'openai', 'ollama'],
                    **kwargs):
        endpoint = os.environ['LLM_API_ENDPOINT']
        api_key = os.environ['LLM_API_KEY']
        assert endpoint and api_key

        if provider == 'ibm':
            if project_id:=kwargs.get('project_id'):
                os.environ['LLM_API_KEY']
                from langchain_ibm import ChatWatsonx
                return ChatWatsonx(
                    model_id=model_name,
                    apikey=api_key, # type: ignore
                    url=endpoint, # type: ignore
                    project_id=project_id,
                )
            raise ValueError(f'Project ID not found while initializing IBM models.')
        raise ValueError(f'Could not initialize `{provider}` not exist.')

    def run(self, question,
            few_shots: Optional[list[Example]]) -> LLM_Response:
        return asyncio.run(self.arun(question, few_shots))

    async def arun(self, question,
                   few_shots: Optional[list[Example]]) -> LLM_Response:

        from langchain.prompts import (AIMessagePromptTemplate,
                                       ChatPromptTemplate,
                                       FewShotChatMessagePromptTemplate,
                                       HumanMessagePromptTemplate)
        from langchain_core.messages import AIMessage, SystemMessage

        messages: Sequence[Any] = [SystemMessage(self.system_prompt)]

        if few_shots:

            examples = [asdict(e) for e in few_shots]
            example_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template("{input}"),
                AIMessagePromptTemplate.from_template("{output}"),
            ])
            few_shot_prompt = FewShotChatMessagePromptTemplate(
                example_prompt=example_prompt,
                examples=examples,
            )

            messages.append(few_shot_prompt)

        messages.append(
            HumanMessagePromptTemplate.from_template("{question}"))

        prompt = ChatPromptTemplate.from_messages(messages)
        debug_chain = RunnableLambda(lambda entry:
                                     (logging.info(entry), entry)[1])

        def remove_think_and_keep_rest(text) -> str:
            import re

            # Remove <think>...</think> for instance deepseek
            if isinstance(text, AIMessage):
                text = text.content
            elif isinstance(text, str):
                text = text
            else:
                raise TypeError(f'Expected AIMessage or str, got {type(text)}')
            cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            return cleaned.strip()

        remove_think = RunnableLambda(remove_think_and_keep_rest)
        chain = prompt | debug_chain | self.model | debug_chain | remove_think | debug_chain | self.parser

        try:
            return await chain.ainvoke({'question': question})
        except Exception as e:
            logging.error(
                f'Question2Triples: Failed while processing, question={question}: {e}'
            )
            raise e
