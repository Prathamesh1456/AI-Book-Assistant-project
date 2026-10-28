"""Firebase Admin: verify ID tokens and persist per-user book data in Firestore."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, auth, firestore
from google.cloud.firestore import Query

logger = logging.getLogger(__name__)

_app = None
_db = None

# Firestore document size limit is ~1 MiB total; keep text field safely below that.
MAX_STORED_TEXT_CHARS = 950_000


def _project_root() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def service_account_path() -> str | None:
    raw = (os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH') or '').strip()
    if not raw:
        return None
    path = raw if os.path.isabs(raw) else os.path.join(_project_root(), raw)
    return path if os.path.isfile(path) else None


def is_firebase_configured() -> bool:
    return service_account_path() is not None


def get_app():
    global _app
    if _app is not None:
        return _app
    path = service_account_path()
    if not path:
        raise RuntimeError(
            'Firebase Admin is not configured. Set FIREBASE_SERVICE_ACCOUNT_PATH in .env '
            'to your service account JSON file path.'
        )
    cred = credentials.Certificate(path)
    _app = firebase_admin.initialize_app(cred)
    logger.info('Firebase Admin initialized')
    return _app


def get_db():
    global _db
    get_app()
    if _db is None:
        _db = firestore.client()
    return _db


def verify_id_token(id_token: str) -> dict:
    get_app()
    return auth.verify_id_token(id_token)


def save_user_book(uid: str, email: str | None, pdf_name: str, extracted_text: str, stored_filename: str | None):
    db = get_db()
    user_ref = db.collection('users').document(uid)
    current_book_ref = user_ref.collection('library').document('current')
    history_ref = user_ref.collection('library').document('history')
    now = datetime.now(timezone.utc)

    text = extracted_text or ''
    truncated = len(text) > MAX_STORED_TEXT_CHARS
    if truncated:
        text = text[:MAX_STORED_TEXT_CHARS]

    # Save current book
    user_ref.set(
        {
            'email': email or '',
            'updatedAt': now,
        },
        merge=True,
    )
    current_book_ref.set(
        {
            'pdfName': pdf_name,
            'extractedText': text,
            'truncated': truncated,
            'charCount': len(text),
            'storedFilename': stored_filename or '',
            'updatedAt': now,
        }
    )

    # Add to history
    book_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{pdf_name.replace(' ', '_')[:20]}"
    history_book_ref = history_ref.collection('documents').document(book_id)
    history_book_ref.set(
        {
            'pdfName': pdf_name,
            'extractedText': text,
            'truncated': truncated,
            'charCount': len(text),
            'storedFilename': stored_filename or '',
            'uploadedAt': now,
            'bookId': book_id,
        }
    )
    
    return {'truncated': truncated, 'char_count': len(text)}


def get_user_document_history(uid: str, limit: int = 10) -> list:
    """Get user's document history."""
    db = get_db()
    history_ref = db.collection('users').document(uid).collection('library').document('history').collection('documents')
    
    # Get documents ordered by upload date (newest first)
    docs = history_ref.order_by('uploadedAt', direction=Query.DESCENDING).limit(limit).get()
    
    history = []
    for doc in docs:
        data = doc.to_dict() or {}
        history.append({
            'bookId': data.get('bookId', ''),
            'pdfName': data.get('pdfName', ''),
            'charCount': data.get('charCount', 0),
            'uploadedAt': data.get('uploadedAt'),
            'truncated': data.get('truncated', False),
        })
    
    return history


def load_historical_document(uid: str, book_id: str) -> dict:
    """Load a specific historical document."""
    db = get_db()
    doc = db.collection('users').document(uid).collection('library').document('history').collection('documents').document(book_id).get()
    
    if not doc.exists:
        return {'extracted_text': '', 'pdf_name': '', 'stored_filename': '', 'truncated': False}
    
    d = doc.to_dict() or {}
    return {
        'extracted_text': d.get('extractedText') or '',
        'pdf_name': d.get('pdfName') or '',
        'stored_filename': d.get('storedFilename') or '',
        'truncated': bool(d.get('truncated')),
    }


def delete_historical_document(uid: str, book_id: str) -> str:
    """Delete a historical document and return the stored filename."""
    db = get_db()
    doc_ref = db.collection('users').document(uid).collection('library').document('history').collection('documents').document(book_id)
    
    # Get the stored filename before deleting
    doc = doc_ref.get()
    stored_filename = ''
    if doc.exists:
        stored_filename = (doc.to_dict() or {}).get('storedFilename') or ''
    
    # Delete the document
    doc_ref.delete()
    return stored_filename


def load_user_book(uid: str) -> dict:
    db = get_db()
    doc = db.collection('users').document(uid).collection('library').document('current').get()
    if not doc.exists:
        return {'extracted_text': '', 'pdf_name': '', 'stored_filename': '', 'truncated': False}
    d = doc.to_dict() or {}
    return {
        'extracted_text': d.get('extractedText') or '',
        'pdf_name': d.get('pdfName') or '',
        'stored_filename': d.get('storedFilename') or '',
        'truncated': bool(d.get('truncated')),
    }


def clear_user_book(uid: str):
    db = get_db()
    snap = db.collection('users').document(uid).collection('library').document('current').get()
    stored = ''
    if snap.exists:
        stored = (snap.to_dict() or {}).get('storedFilename') or ''
    db.collection('users').document(uid).collection('library').document('current').delete()
    return stored
