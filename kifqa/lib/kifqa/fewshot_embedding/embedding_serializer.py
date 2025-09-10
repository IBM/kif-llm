# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import pickle
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional, Union

from kifqa.model.example import Example

from .loaders.abc import BaseLoader


class EmbeddingSerializer:

    def __init__(
            self,
            loader: BaseLoader,
            model: Optional[Any] = None):
        if not model:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as err:
                raise ImportError(
                    f'{__name__} requires SentenceTransformer') from err
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.loader = loader

    def process_data(
            self, input_path: Union[str, Path],
            parser_fn: Callable[[Any], Example]) -> Iterator[Dict[str, Any]]:
        input_path = Path(input_path)
        for example in self.loader.load(input_path, parser_fn):
            yield {
                'input': example.input,
                'output': example.output,
                'embedding': self.model.encode(example.input, convert_to_numpy=True)
            }

    def save_to_pickle(
            self,
            input_path: Union[str, Path],
            output_path: Union[str, Path],
            parser_fn: Callable[[Any], Example]) -> None:
        all_data = self.run(input_path, parser_fn)
        with open(output_path, 'wb') as f:
            pickle.dump(all_data, f)

    def run(
            self, input_path: Union[str, Path],
            parser_fn: Callable[[Any], Example]) -> list[Dict[str, Any]]:
        return [*self.process_data(input_path, parser_fn)]
