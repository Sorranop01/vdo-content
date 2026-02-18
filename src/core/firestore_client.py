"""
Firestore Client Configuration
Initializes the Firestore client using Application Default Credentials (ADC)
or a service account if provided (though ADC is preferred for Cloud Run).
"""

import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as google_firestore

logger = logging.getLogger("vdo_content.database")

# Global client instance
_db_client = None

def get_firestore_client() -> google_firestore.Client:
    """Get or initialize the Firestore client"""
    global _db_client
    
    if _db_client is not None:
        return _db_client
        
    try:
        # Check if Firebase app is already initialized
        try:
            app = firebase_admin.get_app()
        except ValueError:
            # Initialize new app
            # For Cloud Run, no creds needed (uses ADC)
            # For local dev, ensure GOOGLE_APPLICATION_CREDENTIALS is set
            
            project_id = os.getenv("FIREBASE_PROJECT_ID", "vdo-content-4e158")
            
            # Use specific project ID
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': project_id,
            })
            
        _db_client = firestore.client()
        logger.info(f"Firestore client initialized (Project: {os.getenv('FIREBASE_PROJECT_ID', 'vdo-content-4e158')})")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        raise

def get_db():
    """Consistency alias for get_db() pattern used in the app, 
    but returns the Firestore client directly (not a context manager usually, 
    but we can make it one if needed for compatibility, strictly though 
    Firestore client is thread-safe and reusable).
    
    Old usage: with get_db() as db:
    """
    return FirestoreContext()

class FirestoreContext:
    """Context manager adapter for Firestore to maintain 'with get_db() as db:' syntax"""
    def __enter__(self):
        self.client = get_firestore_client()
        return self.client
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # No session cleanup needed for Firestore client
        pass
