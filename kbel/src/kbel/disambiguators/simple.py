# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Tuple

from .abc import Candidate, Disambiguator

LOG = logging.getLogger(__name__)


class SimpleDisambiguator(Disambiguator, disambiguator_name='simple'):
    """Simple disambiguator that always returns the first candidate.

    This is the most basic implementation of a disambiguator plugin. It
    ignores the `limit` parameter and selects only the top candidate
    from the provided list.

    Example:
        >>> disamb = SimpleDisambiguator('simple')
        >>> candidates = [
        ...     {"label": "Python", "description": "Programming language", "iri": "https://www.wikidata.org/wiki/Q28865"}
        ... ]
        >>> disamb._disambiguate("Python", candidates, limit=1)
        [('Python', 'Programming language', 'https://www.wikidata.org/wiki/Q28865')]
    """

    def _disambiguate(
        self,
        label,
        candidates: list[Candidate],
        limit: int,
        *args,
        **kwargs) -> list[Tuple[str, str, str]]:
        """Returns the first candidate from the list.

        Args:
            label (str): The label to disambiguate (ignored in this implementation).
            candidates (list[Candidate]): List of candidate entities.
            limit (int): Maximum number of results requested (ignored here).
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list[Tuple[str, str, str]]: A list containing a single tuple with
                the label, description, and IRI of the first candidate.
        """

        if limit > 1:
            LOG.debug('Limit has no effect here. This method always returns the top 1 candidate.')
        label = candidates[0].get('label', '')
        description = candidates[0].get('description', '')
        iri = candidates[0].get('iri')
        return [(label, description, iri)] # type: ignore
