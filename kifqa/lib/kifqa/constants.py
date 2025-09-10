# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from kifqa.model.example import Example

Q2T_DEFAULT_PROMPT = """\
You are responsible for recognizing incomplete subject-predicate-object triple patterns from simple natural language questions
- Subjects are items (e.g., people, organizations, locations), and objects can be either items or literals (e.g., dates, numbers).
- The property describes the relationship between the subject and the object.
- Each triple must have exactly one unknown element, represented as the string "?x".
- Return a Python list of dictionaries, where each dictionary contains exactly one triple, represented as three string values under the keys "subject", "property", and "object".
- Your output must be valid Python syntax only. Do not include any extra explanations or text.

Example format:
[
    {
        "subject": "Item",
        "property": "relation",
        "object": "?x"
    }
]"""


Q2T_DEFAULT_EXAMPLES = [
    Example("When did World War II begin?", """\
[
    {
        "subject": "World War II",
        "property": "begin",
        "object": "?x"
    }
]"""),
    Example("Where was Freddie Mercury born?", """\
[
    {
        "subject": "Freddie Mercury",
        "property": "born",
        "object": "?x"
    }
]"""),
    Example("Who was the creator of the Mona Lisa?", """\
[
    {
        "subject": "Mona Lisa",
        "property": "creator",
        "object": "?x"
    }
]""")]
