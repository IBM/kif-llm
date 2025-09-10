# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

import uuid
from flask import session

# KIFQA's objects per user (can be replaced by Redis in the future)
qa_registry = {}

def get_or_create_user_id() -> str:
    """Ensures each user has a unique user_id stored in the session."""
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    return session["user_id"]

def set_model(qa) -> None:
    """Associates a KIFQA object with the current session."""
    user_id = get_or_create_user_id()
    qa_registry[user_id] = qa

def get_model():
    """Retrieves the KIFQA object for the current session, or None if not configured."""
    user_id = session.get("user_id")
    return qa_registry.get(user_id) if user_id else None
