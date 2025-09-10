# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import jsonify


def status():
    return jsonify({'status': 200})
