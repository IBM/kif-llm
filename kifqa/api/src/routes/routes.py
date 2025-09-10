# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from flask import Blueprint
from src.controllers.query_controller import stores, query

from src.controllers.filter_controller import filter
from src.controllers.config_controller import config
from src.controllers.registry_controller import model
from src.controllers.status_controller import status

blueprint = Blueprint('blueprint', __name__)

blueprint.route('/status', methods=['GET'])(status)
blueprint.route('/stores', methods=['GET'])(stores)
blueprint.route('/config', methods=['POST'])(config)
blueprint.route('/query', methods=['POST'])(query)
blueprint.route('/filter', methods=['POST'])(filter)
blueprint.route('/model', methods=['GET'])(model)
