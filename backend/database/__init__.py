# database/__init__.py

from .chroma_client import (
    initialize_chroma_db,
    load_static_documents,
    get_client,
    get_collection,
    add_document,
    get_document,
    query_documents,
    update_document,
    delete_document
)
initialize_chroma_db()

