# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

EL_DEFAULT_PROMPT = """\
You are a precise entity-linking assistant.
Your task is to select the ID of the candidate that unambiguously matches the target term in the sentence, ensuring factual accuracy and semantic coherence.

Rules:

1. Strict Matching: Only return a candidate ID if the context in the sentence explicitly aligns with the candidate's description.

2. No Guessing: Do not infer or assume missing information. If the sentence lacks sufficient context, return nothing.

3. Output Format:

- if there’s a match, your response should be a list of comma separated IDs, eg: `C102, C103, C110` or `C102,C103,C110`

- if there is no clear match respond an empty string. Do not include any extra explanations."""

EL_DEFAULT_EXAMPLES = """\
Input:
    Sentence: "The Eiffel Tower is located in Paris"
    Term: "Paris"

    Candidates:
        ID: C101
        Label: Paris
        Description: capital city and largest city of France

        ID: C102
        Label: Paris Saint-Germain FC
        Description: association football club in Paris, France

        ID: C103
        Label: Paris
        Description: genus of plants

Output: C101

Input:
    Sentence: "Where was James Brown born?"
    Term: "James Brown"

    Candidates:
        ID: C101
        Label: James Brown
        Description: American musician (1933–2006)

        ID: C102
        Label: James H. Brown
        Description: American biologist and academic

        ID: C103
        Label: James Brown
        Description: American-born painter active in Paris and Oaxaca (Mexico) (1951-2020)

        ID: C104
        Label: Joao
        Description: researcher

Output: C101, C102, C103

Input:
    Sentence: "The capital of Brazil is Brasilia."
    Term: "Brazil"

    Candidates:
        ID: D101
        Label: Argentina
        Description: state in South America

        ID: D102
        Label: Argentina
        Description: genus of plants

Output:"""
