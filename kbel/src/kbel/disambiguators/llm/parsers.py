# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from langchain_core.output_parsers import CommaSeparatedListOutputParser
from typing_extensions import override


class CommaSeparatedListOutputParserSet(CommaSeparatedListOutputParser):

    @override
    def parse(self, text: str) -> list[str]:
        """Parse the output of an LLM call.

        Args:
            text: The output of an LLM call.

        Returns:
            A list of strings.
        """
        try:
            parts = []
            buffer = ''
            inside_uri = False

            for part in text.split(','):
                part = part.strip()
                if part.startswith('http://') or part.startswith('https://'):
                    if inside_uri:
                        parts.append(buffer.strip())
                    buffer = part
                    inside_uri = True
                elif inside_uri:
                    buffer += ',' + part
                else:
                    parts.append(part)
            if buffer:
                parts.append(buffer.strip())
            return list(dict.fromkeys(parts))
        except Exception as e:
            raise e
