from pathlib import Path
from typing import Any, Callable, Iterator

from kifqa.model.example import Example

from .abc import BaseLoader


class CsvLoader(BaseLoader):



    def load(self, path: Path,
             parser_fn: Callable[[Any], Example], *args, **kwargs) -> Iterator[Example]:
        import csv
        with path.open("r", newline="", encoding="utf-8") as infile:
            dict_reader = csv.DictReader(infile, *args, **kwargs)
            for row_dict in dict_reader:
                parsed = parser_fn(row_dict)
                yield parsed
