# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import request, jsonify
from src.utils.decorators import require_qa

from src.services.query_service import (
    query as query_service)

def stores():
    # stores = list_stores()

    stores = [
            { 'id': 'wdqs', 'description': 'Wikidata' },
            { 'id': 'dbpedia', 'description': 'DBpedia' },
            { 'id': 'pubchem', 'description': 'PubChem' },
        ]

    return jsonify(stores)

@require_qa
def query(model):
    data = request.get_json()
    question = data.get('query')
    if not query:
        raise ValueError("No query provided")
    annotated = data['annotated']
    stores = data.get('stores')
    if not stores:
        raise ValueError("No stores provided")

    for store in stores:
        stmts = query_service(model, question, annotated, store)
        return jsonify(stmts)
