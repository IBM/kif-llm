# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import logging
from textwrap import dedent
from typing import Any, Literal, Optional, Tuple

from langchain_core.language_models import BaseChatModel

from ..abc import Candidate, Disambiguator
from .constants import EL_DEFAULT_EXAMPLES, EL_DEFAULT_PROMPT
from .parsers import CommaSeparatedListOutputParserSet
from .utils import build_model

LOG = logging.getLogger(__name__)


class LLM_Disambiguator(Disambiguator, disambiguator_name='llm'):
    """Disambiguator that leverages a large language model (LLM) for entity disambiguation.

    This disambiguator uses a chat-based LLM to select the most appropriate candidate
    entity for a given label. The disambiguation is performed by constructing a prompt
    with candidate information and optional textual context.

    Example:
        >>> disamb = LLM_Disambiguator(
        ...     disambiguator_name='llm',
        ...     model_name='gpt-4',
        ...     model_provider='openai',
        ...     model_endpoint='https://api.openai.com/v1',
        ...     model_apikey='MY_API_KEY'
        ... )
        >>> candidates = [
        ...     {"label": "Python", "description": "Programming language", "iri": "https://www.wikidata.org/wiki/Q28865"},
        ...     {"label": "Python regius", "description": "species of reptile", "iri": "https://www.wikidata.org/wiki/Q464424"}
        ... ]
        >>> disamb._disambiguate("Python", candidates, sentence="Python is used in coding")
        [('Python', 'Programming language', 'https://www.wikidata.org/wiki/Q28865')]
    """

    _model: BaseChatModel

    def __init__(
        self,
        disambiguator_name: str,
        model: Optional[BaseChatModel] = None,
        model_name: Optional[str] = None,
        model_provider: Optional[Literal['ibm', 'openai', 'ollama']] = None,
        model_params: dict[str, Any] = {},
        model_apikey: Optional[str] = None,
        model_endpoint: Optional[str] = None,
    ):
        """Initializes the LLM_Disambiguator.

        Either an existing model can be provided, or it will be built from
        the specified model parameters.

        Args:
            disambiguator_name (str): Name of this disambiguator plugin.
            model (Optional[BaseChatModel]): Pre-initialized LLM model.
            model_name (Optional[str]): Name of the model to load if `model` is None.
            model_provider (Optional[Literal['ibm', 'openai', 'ollama']]): LLM provider.
            model_params (dict[str, Any]): Additional parameters for building the model.
            model_apikey (Optional[str]): API key for model access.
            model_endpoint (Optional[str]): Endpoint for the LLM.
            *args: Additional positional arguments for the base Disambiguator.
            **kwargs: Additional keyword arguments for the base Disambiguator.
        """
        assert disambiguator_name == self.disambiguator_name
        super().__init__()

        if model:
            self._model = model
        else:
            assert model_name and model_provider and model_endpoint and model_apikey
            _model = build_model(
                model_name=model_name,
                provider=model_provider,
                endpoint=model_endpoint,
                apikey=model_apikey,
                **model_params)

            assert _model
            self._model = _model

    @property
    def model(self) -> BaseChatModel:
        return self._model

    def _disambiguate(
        self,
        label: str,
        candidates: list[Candidate],
        limit=100,
        *args,
        **kwargs,
    ) -> list[Tuple[str, str, str]]:
        """Disambiguates a label using the LLM.

        Args:
            label (str): The label to disambiguate.
            candidates (list[Candidate]): List of candidate entities.
            *args: Additional positional arguments.
            **kwargs: Keyword arguments, including:
                - sentence (str): Sentence containing the term.
                - textual_context (str, optional): Optional context to guide the LLM.

        Returns:
            list[Tuple[str, str, str]]: List of tuples with (label, description, iri)
                of the selected candidates.
        """

        assert label, 'Label can not be undefined.'

        sentence = kwargs.get('sentence')
        assert sentence
        textual_context = kwargs.get('textual_context')

        return self.__llm_entity_disambiguation(
            label,
            candidates,
            sentence,
            textual_context,
            limit=limit)

    def __llm_entity_disambiguation(
            self,
            label: str,
            candidates: list[Candidate],
            sentence: str,
            textual_context: Optional[str] = None,
            limit: Optional[int] = None
    ) -> list[Tuple[str, str, str]]:
        """Internal method that executes the LLM-based disambiguation.

        Constructs a prompt with candidates and optional context, invokes the LLM,
        parses the output, and returns the selected candidate(s).

        Args:
            label (str): Label to disambiguate.
            candidates (list[Candidate]): Candidate entities.
            sentence (str): Sentence containing the label.
            textual_context (Optional[str]): Optional textual context.

        Returns:
            list[Tuple[str, str, str]]: List of tuples containing the label,
                description, and IRI of the top candidates.

        Raises:
            ValueError: If the LLM cannot disambiguate the label among the candidates.
        """
        assert candidates and len(candidates) > 0, f'No candidates to disambiguate the label `{label}`'
        try:
            c_prompt = ''
            for candidate in candidates:
                c_prompt += f'        ID: {candidate["id"]}'

                c_label = candidate.get("label")
                if label:
                    c_label = c_label.strip()
                    c_prompt += f'\n        Label: {c_label}'
                description = candidate.get("description")
                if description:
                    description = description.strip()
                    c_prompt += f'\n        Description: {description}'  # noqa E501
                c_prompt += '\n\n'
            s_template = EL_DEFAULT_PROMPT + '\n\nExamples:\n' + EL_DEFAULT_EXAMPLES
            context_template = 'Context: {context}' if textual_context else ''
            u_template = dedent(f"""Now follow the format strictly.\n
Input:
    Sentence: "{{sentence}}"
    Term: "{{term}}"
    {context_template}

    Candidates:
{{candidates}}
Output:""")
            from langchain_core.prompts import ChatPromptTemplate
            promp_template = ChatPromptTemplate.from_messages([
                ('system', s_template), ('human', u_template)
            ])

            from langchain_core.runnables import RunnableLambda

            debug = RunnableLambda(lambda entry:
                                    (LOG.debug(entry), entry)[1])

            parser = CommaSeparatedListOutputParserSet()
            chain = (promp_template
                        | debug
                        | self.model
                        | debug
                        | parser
                        | debug)

            sentence = sentence
            entity_ids = chain.invoke({
                'context': textual_context,
                'sentence': sentence,
                'term': label,
                'candidates': c_prompt,
            })
            if entity_ids:
                disamb_entities = []
                for entity_id in entity_ids:
                    for c in candidates:
                        c_id = c.get('id')
                        if c_id:
                            if entity_id == c_id:
                                description = c.get('description')
                                disamb_entities.append(
                                    (c['label'], description, c['iri']))
                return disamb_entities[:limit] if limit else disamb_entities
            raise ValueError(f'Could not disambiguate label `{label}` among the candidates.')

        except Exception as e:
            logging.warning(f'Exceptions occured while disambiguating label `{label}`: {e}')
            raise e
