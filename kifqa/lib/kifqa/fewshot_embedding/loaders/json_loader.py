import json
from pathlib import Path
from typing import Any, Callable, Iterator

from kifqa.model.example import Example

from .abc import BaseLoader


class JsonLoader(BaseLoader):

    def load(
        self, path: Path,
        parser_fn: Callable[[Any], Example]) -> Iterator[Example]:
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            yield parser_fn(raw)
