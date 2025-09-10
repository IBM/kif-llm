# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from kif_lib import (IRI, Context, Filter, Store)

from kif_lib.namespace.wikidata import Wikidata
from kif_lib.namespace.dbpedia import DBpedia


def filter(filters: list[Filter], annotated: bool, store: str):
    kb = Store(store)

    ctx = Context.top()
    ctx.options.entities.resolve = True

    ctx.iris.register(IRI(str(Wikidata)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.ONTOLOGY)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.PROPERTY)), resolver=kb)
    ctx.iris.register(IRI(str(DBpedia.RESOURCE)), resolver=kb)

    statements = []
    if filters:
        for filter in filters:
            try:
                stmts = list(kb.filter_annotated(filter=filter) if annotated else kb.filter(filter=filter))
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
            except Exception as e:
                raise e
    return statements
