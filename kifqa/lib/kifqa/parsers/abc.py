# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import TypeVar

from langchain_core.output_parsers import BaseOutputParser
from typing_extensions import override

T = TypeVar("T")


class PromptOutputParser(BaseOutputParser):

    @abstractmethod
    def parse(self, text: str) -> T:
        """Parse a single string model output into some structure.

        Args:
            text: String output of a language model.

        Returns:
            Structured output.
        """
        raise NotImplementedError

    @override
    def get_format_instructions(self) -> str:
        """Instructions on how the LLM output should be formatted."""
        raise NotImplementedError
