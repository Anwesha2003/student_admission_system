import chromadb
from chromadb.config import Settings
import os
from typing import Dict, List, Any, Optional
import json
from chromadb.utils import embedding_functions

# Global client instance
_client = None
_collections = {}

def get_client():
    """Get or create the ChromaDB client"""
    global _client
    if _client is None:
        persist_directory = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
        # Updated Settings object for ChromaDB 0.4.15
        _client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False  # Disable telemetry if not required
        ))
    return _client

def get_collection(name: str, create_if_not_exists: bool = True):
    """Get or create a collection"""
    global _collections
    if name not in _collections:
        client = get_client()
        try:
            _collections[name] = client.get_collection(name)
        except ValueError:
            if create_if_not_exists:
                _collections[name] = client.create_collection(name)
            else:
                raise
    return _collections[name]

def initialize_chroma_db():
    """Initialize ChromaDB with necessary collections"""
    # Create collections for each data type
    get_collection("admissions")
    get_collection("documents")
    get_collection("students")
    get_collection("loans")
    get_collection("eligibility_criteria")
    get_collection("admission_procedures")
    get_collection("fee_structure")
    get_collection("university_policies")
    
    # Load initial data for static documents if needed
    load_static_documents()
    
    print("ChromaDB initialized successfully")

def load_static_documents():
    """Load static documents into the database"""
    # Example for loading eligibility criteria
    eligibility_collection = get_collection("eligibility_criteria")
    
    # Check if collection is empty
    if eligibility_collection.count() == 0:
        sample_criteria = [
            {
                "program": "Computer Science",
                "min_gpa": 6.5,
                "required_subjects": "Mathematics, Computer Science",  # Converted list to comma-separated string
                "additional_requirements": "Programming experience preferred"
            },
            {
                "program": "Business Administration",
                "min_gpa": 5.0,
                "required_subjects": "Economics, Mathematics",  # Converted list to comma-separated string
                "additional_requirements": "Leadership experience preferred"
            }
        ]
        
        eligibility_collection.add(
            ids=[f"criteria_{i}" for i in range(len(sample_criteria))],
            documents=[json.dumps(doc) for doc in sample_criteria],
            metadatas=sample_criteria
        )
    
    # Similarly, load other static documents
    # This is just an example - you would load actual data in production

def add_document(collection_name: str, document: Dict[str, Any], document_id: str, metadata: Optional[Dict[str, Any]] = None):
    """Add a document to a collection"""
    collection = get_collection(collection_name)
    collection.add(
        ids=[document_id],
        documents=[json.dumps(document)],
        metadatas=[metadata] if metadata else None
    )
    return document_id

def get_document(collection_name: str, document_id: str):
    """Get a document from a collection by ID"""
    collection = get_collection(collection_name)
    result = collection.get(ids=[document_id])
    if result and result['documents'] and result['documents'][0]:
        return json.loads(result['documents'][0])
    return None


def query_documents(collection_name: str, query: str, n_results: int = 5, metadata_filter: Optional[Dict[str, Any]] = None):
    """Query documents in a collection"""
    collection = get_collection(collection_name)
    
    # Handle multiple filters and complex conditions
    if metadata_filter:
        processed_filters = []
        
        # Process each field in the metadata filter
        for field, condition in metadata_filter.items():
            if isinstance(condition, dict):
                # Handle complex filters like {"$gte": 18, "$lte": 21}
                for operator, value in condition.items():
                    processed_filters.append({field: {operator: value}})
            elif isinstance(condition, list):
                # Handle multiple values for a single field (e.g., field IN [value1, value2])
                for value in condition:
                    processed_filters.append({field: value})
            else:
                # Handle simple filters like {"field": "value"}
                processed_filters.append({field: condition})
        
        # Combine results for each processed filter
        results = []
        for processed_filter in processed_filters:
            partial_results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=processed_filter
            )
            results.extend(partial_results['documents'][0])
        
        # Remove duplicates and parse JSON
        unique_documents = {doc for doc in results if doc}  # Use a set to remove duplicates
        documents = [json.loads(doc) for doc in unique_documents]
    else:
        # No filter, proceed normally
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=None
        )
        
        documents = []
        for doc in results['documents'][0]:
            if doc:
                documents.append(json.loads(doc))
    
    return documents

def update_document(collection_name: str, document_id: str, document: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
    """Update a document in a collection"""
    collection = get_collection(collection_name)
    collection.update(
        ids=[document_id],
        documents=[json.dumps(document)],
        metadatas=[metadata] if metadata else None
    )
    return document_id

def delete_document(collection_name: str, document_id: str):
    """Delete a document from a collection"""
    collection = get_collection(collection_name)
    collection.delete(ids=[document_id])
    return True