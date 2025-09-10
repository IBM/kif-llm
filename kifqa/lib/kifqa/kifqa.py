# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import dataclasses
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterator, Literal, Optional, Tuple, TYPE_CHECKING

import numpy as np
import yaml
from kif_lib import (Entity, Filter, Item, ItemDatatype, Property, Search,
                     Statement, Store, Value)
from kif_lib.vocabulary import wd
from langchain_core.language_models.chat_models import BaseChatModel
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from kbel.disambiguators import Disambiguator
from kifqa.fewshot_embedding.embedding_serializer import EmbeddingSerializer
from kifqa.model.example import Example
from kifqa.q2t import QuestionToTriples, Triples
from kifqa.utils import build_model


RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', 3))

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@dataclasses.dataclass
class LLM_ModelBuilder:
    provider: Literal['ibm', 'openai', 'ollama']
    model_name: str
    model_params: Optional[dict[str, Any]] = None


class Q2T_Options:
    model: LLM_ModelBuilder | BaseChatModel
    few_shot_embedding_space: str


class EL_Options:
    model: LLM_ModelBuilder | BaseChatModel


class KIFQA:
    _q2t: QuestionToTriples
    _q2t_model: Optional[BaseChatModel] = None
    _q2t_prompt: str
    _q2t_examples: Optional[list[Example]] = None
    _q2t_labels: list = []
    _el_model: Optional[BaseChatModel] = None
    _el_prompt: str
    _el_examples: Optional[list[Example] | str] = None
    _store: Store
    _disambiguator: Disambiguator
    _disambiguated_labels: list[Tuple] = []
    _triples: list[Tuple] = []
    _triple_pattern: list[Triples] = []
    _kif_filters: list[Filter] = []
    _items: list[Tuple[str, str, Item]] = []
    _properties: list[Tuple[str, str, Property]] = []
    _fewshot_embeddings_data: Optional[Any] = None
    _fewshot_embeddings: Optional[Any] = None
    _embedding_model: Optional[SentenceTransformer] = None
    _search: Search


    @property
    def store(self):
        return self._store

    @store.setter
    def store(self, value: Store):
        self._store = value

    @property
    def search(self):
        return self._search

    @search.setter
    def search(self, value: Search):
        self._search = value

    @property
    def disambiguated_labels(self):
        return self._disambiguated_labels

    @property
    def triples(self):
        return self._triples

    @property
    def items(self):
        return self._items

    @property
    def properties(self):
        return self._properties

    @property
    def q2t_labels(self):
        return self._q2t_labels

    @property
    def triple_pattern(self):
        return self._triple_pattern

    @property
    def q2t_examples(self):
        return self._q2t_examples

    @property
    def kif_filters(self):
        return self._kif_filters

    def __init__(
            self,
            store: Store,
            search: Search,
            model_name: Optional[str] = None,
            model_provider: Optional[Literal['ibm', 'openai', 'ollama']] = None,
            model_apikey: Optional[str] = None,
            model_endpoint: Optional[str] = None,
            model_params: dict[str, Any] = {},
            model: Optional[BaseChatModel] = None,
            q2t_model: Optional[BaseChatModel] = None,
            disambiguator: Optional[Disambiguator] = None,
            el_model: Optional[BaseChatModel] = None,
            *args, **kwargs):

        if not model_params:
            model_params = {}

        self._store = store
        self._search = search

        if model:
            self._q2t_model = model
            self._el_model = model
        else:
            assert model_provider, 'Please, select a LLM provider: `ibm`, `openai` or `ollama`'
            assert model_name, 'No model name provided'
            assert model_endpoint, 'Please, provide the LLM endpoint'
            assert model_apikey, 'No apikey was provided.'

            _model = build_model(
                model_name=model_name,
                provider=model_provider,
                endpoint=model_endpoint,
                apikey=model_apikey,
                **model_params)
            self._q2t_model = _model
            self._el_model = _model

        if q2t_model:
            self._q2t_model = q2t_model
        if el_model:
            self._el_model = el_model

        assert self._q2t_model and self._el_model

        if disambiguator:
            self._disambiguator = disambiguator
        else:
            from kbel.disambiguators.llm import LLM_Disambiguator
            self._disambiguator = Disambiguator('llm', model=self._el_model)


    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def _filter_properties_by_item(self, filter):
        it = self._store.filter_p(filter=filter)
        return list(it)

    def _search_properties_by_item(self, subject, property, object):
        candidate_properties = None
        try:
            if subject:
                candidate_properties = self._filter_properties_by_item(
                    filter=Filter(
                        subject=subject,
                        snak_mask=Filter.VALUE_SNAK,
                        property_mask=Filter.REAL,
                        value_mask=Filter.VALUE & ~Filter.EXTERNAL_ID))
            elif object:
                candidate_properties = self._filter_properties_by_item(
                    filter=Filter(value=object, property_mask=Filter.REAL))
        except RetryError as e:
            le = e.last_attempt.exception()
            raise le if le else e
        except Exception as e:
            raise e

        candidates = []
        if not candidate_properties:
            raise ValueError(
                f'Could not fetch candidates for label `{property}`.')
        for property_candidate in candidate_properties:
            if property_candidate and property_candidate.label:
                p_candidate_label = property_candidate.label.content
                candidate = {
                    'id': property_candidate.iri.content,
                    'label': p_candidate_label,
                    'iri': property_candidate.iri.content,
                }
                p_description = property_candidate.description
                if p_description:
                    candidate['description'] = p_description.content
                candidates.append(candidate)

        return candidates

    def _full_disambiguate_property(
        self,
        property_label: str,
        question: str,
        subject: Optional[Item] = None,
        object: Optional[Item] = None,
        description: Optional[str] = None,
    ) -> Optional[list[Tuple[str, str, Property]]]:
        try:
            candidates = []
            candidates += self._search_properties_by_item(
                subject, property_label, object)
            if not candidates:
                return None
            candidates = list({d['id']: d
                               for d in reversed(candidates)}.values())[::-1]
            try:

                return self._disambiguator.disambiguate_candidates(
                    label=property_label,
                    candidates=candidates,
                    cls=Property,
                    textual_context=description,
                    sentence=question)
            except RetryError as e:
                le = e.last_attempt.exception()
                raise le if le else e

        except Exception as e:
            logging.info(
                f'Could not fetch properties for label `{property_label}`: {e}'
            )
            raise e

    def item_linking(
            self,
            label: str,
            question: str,
            candidates_limit=10) -> list[Tuple[str, str, Item]]:
        try:
            self.search.limit = candidates_limit
            items = self._disambiguator.disambiguate_item(
                label=label,
                searcher=self.search,
                sentence=question)
            if items:
                return items
            raise ValueError(f'Could not disambiguate item ({label})')
        except RetryError as e:
            le = e.last_attempt.exception()
            raise le if le else e
        except Exception as e:
            logging.exception(e)
            raise e

    def _handle_constraints(self, triple: Triples, question):
        constraints = []
        constraint_labels = []
        oc_label = None
        pc_label = None
        if triple.constraints:
            for constraint in triple.constraints:
                pc = None
                oc_label, oc_description, oc = self.item_linking(
                    triple.object, question)
                if oc:
                    if constraint.property == 'a':
                        pc = wd.a
                    else:
                        pc_disambiguated = self._full_disambiguate_property(
                            property_label=constraint.property,
                            question=question,
                            subject=None,
                            object=oc)
                        if pc_disambiguated:
                            pc_label, pc_description, pc = pc_disambiguated

                constraints.append((None, pc, oc))
                constraint_labels.append((None, pc_label, oc_label))
        return constraint_labels, constraints

    def _resolve_property_label(self, triple: Triples):
        """Search for the best property match by label using kif search."""
        if triple.property:
            properties = self.search.property_descriptor(triple.property, candidates_limit=10)
            for prop, desc in properties:
                label = desc.get('labels', {}).get('en')
                if label and label.content == triple.property:
                    description = desc.get('descriptions', {}).get('en', '').content if 'descriptions' in desc else ''
                    return (label.content, description, prop)
        return None

    def _generate_filters_by_property_search(self, triple: Triples, disam_items, constraint_labels, constraints):
        """Attempt to resolve the property directly and generate filters without full disambiguation."""
        try:
            disambiguated_property = self._resolve_property_label(triple)
            if not disambiguated_property:
                return None

            filters = []
            for item in disam_items:
                if triple.object != '?x':  # subject is the disambiguated entity
                    disamb_triple = (None, disambiguated_property[2], item[2], constraints)
                    labels = (None, disambiguated_property[0], item[0], constraint_labels)
                else:  # object is the disambiguated entity
                    disamb_triple = (item[2], disambiguated_property[2], None, constraints)
                    labels = (item[0], disambiguated_property[0], None, constraint_labels)

                self._triples.append(disamb_triple)
                self._disambiguated_labels.append(labels)

                if f := self.to_filter(disamb_triple):
                    filters.append(f)

            self._kif_filters = filters
            return filters
        except Exception as e:
            logging.warning(
                f'Attempt to resolve the property directly and generate filters without full disambiguation failed: {e}')
            return None

    def _get_item_role(self, triple: Triples):
        """Determine which entity (subject or object) needs to be disambiguated."""
        if triple.object != '?x':
            return 'subject', triple.object
        return 'object', triple.subject

    def _generate_filters_with_disambiguation(self,
            triple: Triples, disam_items, question: str, constraint_labels, constraints, to_be_found
        ):
        """Fallback to full property disambiguation for each disambiguated item."""
        def disambiguate_one_property(s, sl, sd, p, o, ol):
            disamb_props = self._full_disambiguate_property(
                property_label=p,
                subject=s,
                object=o,
                question=question,
                description=sd
            )
            if not disamb_props:
                raise ValueError(f'Could not disambiguate property {p}')

            for label, desc, prop in disamb_props:
                if (label, desc, prop) not in self._properties:
                    self._properties.append((label, desc, prop))
                disamb_triple = (s, prop, o, constraints)
                labels = (sl, label, ol, constraint_labels)
                self._triples.append(disamb_triple)
                self._disambiguated_labels.append(labels)
                if f := self.to_filter(disamb_triple):
                    self._kif_filters.append(f)

        with ThreadPoolExecutor() as executor:
            tasks = []
            for item_label, item_desc, item_id in disam_items:
                if to_be_found == 'object':
                    args = (item_id, item_label, item_desc, triple.property, None, None)
                else:
                    args = (None, None, item_desc, triple.property, item_id, item_label)

                tasks.append(executor.submit(disambiguate_one_property, *args))

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    logging.warning(f'Error in threaded disambiguation: {e}')


    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def get_logical_form(self,
                         question,
                         model: Optional[BaseChatModel] = None,
                         model_name: Optional[str] = None,
                         model_provider: Optional[Literal['ibm', 'openai', 'ollama']] = None,
                         model_params: dict[str, Any] = {},
                         few_shot_number=5) -> list[Triples]:
        _model = self._q2t_model
        if model:
            _model = model
        elif model_name and model_provider:
            _model = build_model(
                model_name=model_name,
                provider=model_provider,
                **model_params)

        q2t = QuestionToTriples(model=_model)

        top_results = self._q2t_examples
        if self._fewshot_embeddings_data:
            from sklearn.metrics.pairwise import cosine_similarity
            query_embedding = self._embedding_model.encode(
                question, convert_to_numpy=True)
            scores = cosine_similarity(
                [query_embedding], self._fewshot_embeddings)[0]  # type: ignore
            top_indices = np.argsort(scores)[::-1][:few_shot_number]

            top_results = [
                self._fewshot_embeddings_data[i] for i in top_indices
            ]

            self._q2t_examples = top_results

        triples = q2t.run(question, top_results)
        return triples.root

    def generate_filters(
            self,
            triples: list[Triples],
            question: str,
            edges_only=True):
        self.reset()
        self._q2t_labels = [
            (t.subject, t.property, t.object, t.constraints)
            for t in triples
        ]

        if len(self._q2t_labels) > 1:
            raise ValueError('Error: Multiple draft triples generated.')

        for triple in triples:
            constraint_labels, constraints = self._handle_constraints(
                triple, question)

            property_label = triple.property
            assert property_label

            to_be_found = None
            main_entity = None
            if triple.subject == '?x':
                to_be_found = 'subject'
                main_entity = triple.object
            elif triple.object == '?x':
                to_be_found = 'object'
                main_entity = triple.subject
            else:
                raise ValueError(f'Error: malformed draft triple `{self._q2t_labels}`.')

            if not main_entity:
                raise ValueError(f'Error: malformed draft triple `{self._q2t_labels}`.')

            items = self.item_linking(label=main_entity, question=question)
            self._items = items
            if not items:
                return []

            if not edges_only:
                filters = self._generate_filters_by_property_search(
                    triple, items, constraint_labels, constraints
                )
                if filters:
                    return filters

            to_be_found, main_entity = self._get_item_role(triple)

            self._generate_filters_with_disambiguation(
                triple, items, question, constraint_labels, constraints, to_be_found
            )

        return self._kif_filters

    def to_filter(self, triples: Tuple) -> Optional[Filter]:
        if triples:
            # Must have at least two components
            if sum(x is not None for x in triples) >= 2:
                # TODO fix for multiple constraints (OR, AND...)
                subject = triples[0]
                object = triples[2]
                if triples[3]:
                    for constraint in triples[3]:
                        if not triples[0]:
                            subject = constraint[1](constraint[2])
                        if not triples[2]:

                            object = constraint[1](constraint[2])

                property: Property = triples[1]
                if property.registered_range is not None:
                    if isinstance(property.registered_range, ItemDatatype):
                        return Filter(subject=subject,
                                      property=property,
                                      value=object,
                                      snak_mask=Filter.VALUE_SNAK,
                                      subject_mask=Filter.ITEM,
                                      value_mask=Filter.ITEM, # TODO: remove to allow data values
                                      property_mask=Filter.REAL)
                else:
                    return Filter(subject=subject,
                                  property=property,
                                  value=object,
                                  snak_mask=Filter.VALUE_SNAK,
                                  subject_mask=Filter.ITEM,
                                  value_mask=Filter.ITEM, # TODO: remove to allow data values
                                  property_mask=Filter.REAL)
        return None

    def reset(self):
        self._disambiguated_labels = []
        self._kif_filters = []
        self._q2t_labels = []
        self._triples = []
        self._items = []
        self._properties = []

    def query(
            self,
            question: str,
            *args, **kwargs) -> Iterator[Statement]:
        triples = self.get_logical_form(question)
        self._triple_pattern = triples
        if not triples:
            raise ValueError(f'Could not extract triples from question: `{question}`')
        kif_filters = self.generate_filters(triples=triples, question=question)
        for filter in kif_filters:
            yield from self.filter(filter, *args, **kwargs)

    def query_s(self, question: str, *args, **kwargs) -> Iterator[Entity]:
        triples = self.get_logical_form(question)
        if not triples:
            raise ValueError(f'Could not extract triples from question: `{question}`')
        kif_filters = self.generate_filters(triples=triples, question=question)
        for filter in kif_filters:
            yield from self.filter_s(filter, *args, **kwargs)

    def query_v(self, question: str, *args, **kwargs) -> Iterator[Value]:
        triples = self.get_logical_form(question)
        if not triples:
            raise ValueError(f'Could not extract triples from question: `{question}`')
        kif_filters = self.generate_filters(triples=triples, question=question)
        for filter in kif_filters:
            yield from self.filter_v(filter, *args, **kwargs)

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def filter(
        self,
        filter,
        *args, **kwargs) -> Iterator[Statement]:
        for it in self._store.filter(filter=filter, *args, **kwargs):
            yield it

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def filter_annotated(
        self,
        filter,
        *args, **kwargs) -> Iterator[Statement]:
        for it in self._store.filter_annotated(filter=filter, *args, **kwargs):
            yield it

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def filter_s(
        self,
        filter,
        *args, **kwargs)-> Iterator[Entity]:
        for it in self._store.filter_s(filter=filter, *args, **kwargs):
            yield it

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def filter_v(
        self,
        filter,
        *args, **kwargs) -> Iterator[Value]:
        for it in self._store.filter_v(filter=filter, *args, **kwargs):
            yield it

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def query_annotated(self,
                        question: str,
                        *args, **kwargs) -> Iterator[Statement]:
        triples = self.get_logical_form(question)
        if not triples:
            raise ValueError(f'Could not extract triples from question: `{question}`')
        kif_filters = self.generate_filters(triples=triples, question=question)
        for filter in kif_filters:
            for it in self._store.filter_annotated(filter=filter, *args, **kwargs):
                yield it

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_fixed(1))
    def count(
        self,
        question: str,
        filter: Filter,
        *args, **kwargs) -> int:
        triples = self.get_logical_form(question)
        if not triples:
            raise ValueError(f'Could not extract triples from question: `{question}`')
        kif_filters = self.generate_filters(triples=triples, question=question)
        count = 0
        for filter in kif_filters:
            count += self._store.count(filter=filter, *args, **kwargs)
        return count
