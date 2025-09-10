# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import request, jsonify
from kif_lib import Filter, Item, Property

from src.services.filter_service import (
    filter as filter_service)

def filter():
    data = request.get_json()
    filters = data.get('filters')
    annotated = data['annotated']
    stores = data.get('stores')
    if not stores:
        raise ValueError("No stores provided")
    kif_filters = []
    if filters:
        for filter in filters:
            sub = filter.get('subject')
            obj = filter.get('object')
            prop = filter.get('property')
            subject = None
            object = None
            property = None
            if sub:
                subject = Item(sub.get('iri'))
            if obj:
                object = Item(obj.get('iri'))
            if prop:
                property = Property(prop.get('iri'))
            kif_filter = Filter(subject=subject, property=property, value=object, value_mask=Filter.VALUE)
            kif_filters.append(kif_filter)

    try:
        # TODO create mixer when multiple stores are selected
        stmts = filter_service(kif_filters, annotated, stores[0])
        return jsonify(stmts)
    except Exception as e:
        raise RuntimeError(f"Could not filter KIF-QA: {type(e).__name__}: {e}")
