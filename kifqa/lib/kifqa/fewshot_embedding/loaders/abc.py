from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterator, TypeAlias

from kifqa.model.example import Example


class BaseLoader(ABC):

    Args: TypeAlias = Any

    _kwargs: Any

    def __init__(self, *args: Args, **kwargs: Any) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def load(self, path: Path,
             parser_fn: Callable[[Any], Example]) -> Iterator[Example]:
        ...
