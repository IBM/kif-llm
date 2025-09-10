# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Callable, Literal, Tuple

import numpy as np

from .abc import Candidate, Disambiguator

try:
    from sentence_transformers import SentenceTransformer
except ImportError as err:
    raise ImportError(
        f'{__name__} requires SentenceTransformer') from err

try:
    from sklearn.metrics.pairwise import (cosine_similarity,
                                          euclidean_distances, linear_kernel)
except ImportError as err:
    raise ImportError(
        f'{__name__} requires sklearn') from err

LOG = logging.getLogger(__name__)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0][0])

def dot(a: np.ndarray, b: np.ndarray) -> float:
    return float(linear_kernel(a.reshape(1, -1), b.reshape(1, -1))[0][0])

def euclidean(a: np.ndarray, b: np.ndarray) -> float:
    dist = euclidean_distances(a.reshape(1, -1), b.reshape(1, -1))[0][0]
    return -float(dist)

SIMILARITY_METRICS: dict[str, Callable[[np.ndarray, np.ndarray], float]] = {
    "cosine": cosine,
    "dot": dot,
    "euclidean": euclidean,
}

def to_numpy(vec):
    return vec.detach().cpu().numpy() if hasattr(vec, "detach") else np.asarray(vec)

class SimilarityDisambiguator(Disambiguator, disambiguator_name='sim'):
    """Disambiguator that selects candidates based on embedding similarity.

    This disambiguator uses a sentence embedding model to compute vector
    representations of the input label and candidate entities. It then
    ranks the candidates according to a chosen similarity metric and
    returns the top results.

    Attributes:
        _model (SentenceTransformer): The embedding model used to encode
            the label and candidates.
        _similarity_fn (Callable[[np.ndarray, np.ndarray], float]):
            Function to compute similarity between embeddings.

    Example:
        >>> disamb = SimilarityDisambiguator('sim', model_name='all-MiniLM-L6-v2')
        >>> candidates = [
        ...     {"label": "Python", "description": "Programming language", "iri": "https://www.wikidata.org/wiki/Q28865"},
        ...     {"label": "Python regius", "description": "species of reptile", "iri": "https://www.wikidata.org/wiki/Q464424"}
        ... ]
        >>> disamb._disambiguate("Python", candidates, limit=1, sentence="Python is used in coding")
        [('Python', 'Programming language', 'https://www.wikidata.org/wiki/Q28865')]
    """
    _model: SentenceTransformer
    _similarity_fn: Callable[[np.ndarray, np.ndarray], float]

    def __init__(
        self,
        disambiguator_name: str,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_metric: Literal['cosine', 'dot', 'euclidean'] = 'cosine',
        *args,
        **kwargs,
    ):
        assert disambiguator_name == self.disambiguator_name
        super().__init__(*args, **kwargs)

        LOG.info(f"Loading embedding model: {model_name}")
        self._model = SentenceTransformer(model_name)


        self._similarity_fn = SIMILARITY_METRICS.get(similarity_metric, cosine)


    def _disambiguate(self, label, candidates: list[Candidate], limit: int, *args,
                      **kwargs) -> list[Tuple[str, str, str]]:

        """Disambiguates a label using embedding similarity.

        This method encodes the input label and all candidate labels and
        descriptions using the embedding model, computes similarity scores,
        and returns the top candidates according to the chosen similarity metric.

        Args:
            label (str): The term or sentence to disambiguate.
            candidates (list[Candidate]): List of candidate entities.
            limit (int): Maximum number of top candidates to return.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments, e.g., extra context.

        Returns:
            list[Tuple[str, str, str]]: List of tuples containing the label,
                description, and IRI of the top candidates.
        """

        assert candidates, f"No candidates to disambiguate label `{label}`"

        sentence = label
        sentence_param = kwargs.get("sentence")
        if sentence_param:
            sentence = f'{sentence} {sentence_param}'

        LOG.debug(f"Disambiguating with sentence: {sentence}")
        try:
            sentence_emb = self._model.encode(sentence)
            candidate_texts = [
                (c.get("label", "") or "") + " " + (c.get("description", "") or "")
                for c in candidates
            ]
            candidate_embs = self._model.encode(candidate_texts)

            sims = [
                (self._similarity_fn(to_numpy(sentence_emb), to_numpy(emb)), c)
                for emb, c in zip(candidate_embs, candidates)
            ]

            sims.sort(key=lambda x: x[0], reverse=True)
            top = sims[:limit]

            return [
                (c.get("label", ""), c.get("description", ""), c.get("iri"))
                for _, c in top
            ] # type: ignore

        except Exception as e:
            LOG.warning(f"Error in similarity disambiguation for `{label}`: {e}")
            raise e
