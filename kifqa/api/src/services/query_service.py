# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from kif_lib import IRI, Context, Search, Store
from kif_lib.model import FullFingerprint
from kifqa import KIFQA

from kif_lib.namespace.wikidata import Wikidata
from kif_lib.namespace.dbpedia import DBpedia


def list_stores():
    stores = []

    kif_stores = ((k, v.store_description) for k, v in Store.registry.items())

    for kif_store in kif_stores:
        store = {
            "id": kif_store[0],
            "description": kif_store[1],
        }
        stores.append(store)

    return stores


def query(model, query: str, annotated: bool, store: str):
    kb = Store(store)

    ctx = Context.top()
    ctx.options.entities.resolve = True

    ctx.iris.register(IRI(str(Wikidata)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.ONTOLOGY)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.PROPERTY)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.RESOURCE)), resolver=kb)
    search = Search('wikidata')

    if store == 'dbpedia':
        search = Search('dbpedia')
    if store == 'pubchem':
        search = Search('pubchem')

    kifqa = KIFQA(store=kb, search=search, model=model)

    stmts = kifqa.query_annotated(query) if annotated else kifqa.query(query)
    statements = []
    for stmt in stmts:
        value = stmt.snak.value
        value_label = value.label.content if value.label else value.iri.content

        subject_description = stmt.subject.description.content if stmt.subject.description else stmt.subject.iri.content
        property_description = stmt.snak.property.description.content if stmt.snak.property.description else stmt.snak.property.iri.content
        value_description = stmt.snak.value.description.content if stmt.snak.value.description else stmt.snak.value.iri.content
        statement = {
            "subject": {
                "iri": stmt.subject.iri.content,
                "label": stmt.subject.label.content,
                "description": subject_description
            },
            "snak": {
                "property": {
                    "label": stmt.snak.property.label.content,
                    "iri": stmt.snak.property.iri.content,
                    "description": property_description
                },
                "value": {
                    "label": value_label,
                    "iri": value.iri.content,
                    "description": value_description
                }
            },
        }

        statements.append(statement)

    pattern = kifqa.triple_pattern
    logical_form = [
        {
            "subject": p.subject,
            "predicate": p.property,
            "object": p.object
        }
        for p in pattern
    ]


    items = kifqa.items
    candidate_items = [
        {
            "iri": i[2].iri.content,
            "label": i[0],
            "description": i[1]
        }
        for i in items
    ]

    properties = kifqa.properties

    candidate_properties = [
        {
            "iri": p[2].iri.content,
            "label": p[0],
            "description": p[1] or ''
        }
        for p in properties
    ]

    filters = kifqa.kif_filters
    candidate_filters = []
    for f in filters:
        subject = None
        property = None
        value = None
        if not isinstance(f.subject, FullFingerprint):
            subject_description = f.subject.value.description.content if f.subject.value.description else f.subject.value.iri.content
            subject = {
                'iri': f.subject.value.iri.content,
                'label': f.subject.value.label.content,
                'description': subject_description
            }
        if not isinstance(f.property, FullFingerprint):
            property_description = f.property.value.description.content if f.property.value.description else f.property.value.iri.content
            property = {
                'iri': f.property.value.iri.content,
                'label': f.property.value.label.content,
                'description': property_description
            }
        if not isinstance(f.value, FullFingerprint):
            property = {
                'iri': f.value.value.iri.content,
                'label': f.value.value.label.content,
            }
        candidate_filters.append(
            {
                'subject': subject,
                'property': property,
                'value': value
            }
        )

    return {
        "statements": statements,
        "pattern": logical_form,
        "filters": candidate_filters,
        "items": candidate_items,
        "properties": candidate_properties
    }
