# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import abstractmethod
from typing import (Any, AsyncIterator, ClassVar, Final, Iterator, Optional,
                    Tuple, Type, TypedDict, TypeVar)

from kif_lib import Entity, Item, KIF_Object, Property, Search

LOG = logging.getLogger(__name__)

T = TypeVar("T", bound=Entity)

class Candidate(TypedDict):
    """Represents a candidate entity for disambiguation.

    Attributes:
        iri (str): The IRI of the entity.
        label (str): The label of the entity.
        id (Optional[str]): Optional identifier for the entity.
        description (Optional[str]): Optional description.
        aliases (Optional[list[str]]): Optional list of alias labels.
    """
    iri: str
    label: str
    id: Optional[str]
    description: Optional[str]
    aliases: Optional[list[str]]

class Disambiguator:
    """Base class for entity disambiguators.

    Subclasses must implement the `_disambiguate` method, which contains the
    logic to select the correct entity among a list of candidates.

    Parameters:
        disambiguator_name (str): Name of the disambiguator plugin.
    """

    #: Name of the disambiguation plugin.
    disambiguator_name: ClassVar[str]

    #: Registry of all available disambiguator plugins.
    registry: Final[dict[str, type['Disambiguator']]] = {}

    @classmethod
    def _register(
        cls,
        disambiguator: type['Disambiguator'],
        disambiguator_name: str,
    ):
        """Registers a disambiguator plugin class.

        Args:
            disambiguator (type[Disambiguator]): Disambiguator class.
            disambiguator_name (str): Name to register under.
        """
        disambiguator.disambiguator_name = disambiguator_name
        cls.registry[disambiguator.disambiguator_name] = disambiguator

    @classmethod
    def __init_subclass__(cls, disambiguator_name: str):
        Disambiguator._register(cls, disambiguator_name)

    def __new__(cls, disambiguator_name: str, *args: Any, **kwargs: Any):
        KIF_Object._check_arg(
            disambiguator_name,
            disambiguator_name in cls.registry,
            f'no such disambiguator plugin "{disambiguator_name}"',
            Disambiguator,
            'disambiguator_name',
            1,
            ValueError,
        )
        return super().__new__(
            cls.registry[disambiguator_name])  # pyright: ignore

    def disambiguate_item(
        self,
        label: str,
        searcher: Search,
        limit = 100,
        language = 'en',
        *args: Any,
        **kwargs: Any) -> list[Tuple[str, str, Item]]:
        """Disambiguates a label among Item candidates.

        Args:
            label (str): Label to disambiguate.
            searcher (Search): Search object to retrieve candidates.
            limit (int, optional): Maximum number of candidates to consider. Defaults to 10.
            language (str, optional): Language code for labels/descriptions. Defaults to 'en'.

        Returns:
            list[Tuple[str, str, Item]]: List of disambiguated candidates.
        """
        return self.disambiguate(label, searcher, Item, limit, language, *args, **kwargs)

    def disambiguate_property(
        self,
        label: str,
        searcher: Search,
        limit = 100,
        language = 'en',
        *args: Any,
        **kwargs: Any) -> list[Tuple[str, str, Property]]:
        """Disambiguates a label among Property candidates.

        Args:
            label (str): Label to disambiguate.
            searcher (Search): Search object to retrieve candidates.
            limit (int, optional): Maximum number of candidates to consider. Defaults to 10.
            language (str, optional): Language code for labels/descriptions. Defaults to 'en'.

        Returns:
            list[Tuple[str, str, Property]]: List of disambiguated candidates.
        """
        return self.disambiguate(label, searcher, Property, limit, language, *args, **kwargs)

    def disambiguate(
        self,
        label: str,
        searcher: Search,
        cls: Type[T],
        limit = 10,
        language = 'en',
        *args: Any,
        **kwargs: Any
    ) -> list[Tuple[str, str, T]]:
        """Core method to disambiguate a label among candidates from the knowledge base.

        Args:
            label (str): Label to disambiguate.
            searcher (Search): Search object to retrieve candidates.
            cls (Type[T]): Entity type (Item or Property).
            limit (int, optional): Maximum number of candidates to consider. Defaults to 10.
            language (str, optional): Language code for labels/descriptions. Defaults to 'en'.

        Returns:
            list[Tuple[str, str, T]]: List of tuples with label, description, and entity.
        """

        def safe_next(it: Iterator) -> Iterator:
            """Safely iterate over an iterator, skipping errors."""
            while True:
                try:
                    yield next(it)
                except StopIteration:
                    break
                except Exception as e:
                    logging.info(f'Error fetching item: {e}')
                    continue

        def extract_text(data: dict[str, Any], key: str) -> str:
            """Extract the text for a given key and language."""
            value = data.get(key, {}).get(language)
            return value.content if value else ''

        try:
            if cls is Item:
                found_candidates = searcher.item_descriptor(search=label)
            elif cls is Property:
                found_candidates = searcher.property_descriptor(search=label)
            else:
                return []
        except Exception as e:
            raise e

        if not found_candidates:
            return []

        candidates = []
        for entity, desc in safe_next(iter(found_candidates)):
            candidate = {
                'id': entity.iri.content,
                'label': extract_text(desc, 'labels'),
                'description': extract_text(desc, 'descriptions'),
                'iri': entity.iri.content,
            }
            candidates.append(candidate)

        return self.disambiguate_candidates(label, candidates, cls, limit, *args, **kwargs)

    def disambiguate_candidates(
        self,
        label: str,
        candidates: list[Candidate],
        cls: Type[T],
        limit: int = 10,
        *args: Any,
        **kwargs: Any,
    ) -> list[Tuple[str, str, T]]:
        """Synchronously disambiguates a list of candidates.

        Args:
            label (str): Label to disambiguate.
            candidates (list[Candidate]): Candidate entities.
            cls (Type[T]): Entity type (Item or Property).
            limit (int, optional): Maximum number of candidates to return. Defaults to 10.

        Returns:
            list[Tuple[str, str, T]]: List of tuples with label, description, and entity instance.
        """
        assert len(candidates) > 0, 'No candidates to disambiguate'
        results = self._disambiguate(label, candidates, limit, *args, **kwargs)
        disamb_entities = []
        if results:
            for result in results:
                _label, description, entity = result
                disamb_entities.append((_label, description, cls(iri=entity))) # type: ignore
        return disamb_entities

    async def adisambiguate(
        self,
        label: str,
        candidates: list[Candidate],
        cls: Type[T],
        limit: int = 10,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[Tuple[str, str, T]]:
        """Asynchronously disambiguates a list of candidates.

        Args:
            label (str): Label to disambiguate.
            candidates (list[Candidate]): Candidate entities.
            cls (Type[T]): Entity type (Item or Property).
            limit (int, optional): Maximum number of candidates to return. Defaults to 10.

        Yields:
            AsyncIterator[Tuple[str, str, T]]: Tuples with label, description, and entity instance.
        """
        results = self._disambiguate(label, candidates, limit, *args, **kwargs)
        for label, description, entity in results:
            yield (label, description, cls(iri=entity)) # type: ignore

    @abstractmethod
    def _disambiguate(self, label, candidates: list[Candidate], limit: int, *args,
                      **kwargs) -> list[Tuple[str, str, str]]:
        """Core disambiguation logic to be implemented by subclasses.

        Args:
            label (str): Label to disambiguate.
            candidates (list[Candidate]): List of candidate entities.
            limit (int): Maximum number of results to return.

        Returns:
            list[Tuple[str, str, str]]: Tuples of label, description, and entity identifier.
        """
        ...
