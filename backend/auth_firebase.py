"""Require a valid Firebase ID token on API routes."""

from functools import wraps
import logging

from flask import request, jsonify, g

from firebase_service import is_firebase_configured, verify_id_token

logger = logging.getLogger(__name__)


def require_firebase_user(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method == 'OPTIONS':
            return ('', 204)

        if not is_firebase_configured():
            return jsonify(
                {
                    'success': False,
                    'error': 'Server Firebase is not configured. Add FIREBASE_SERVICE_ACCOUNT_PATH to .env.',
                }
            ), 503

        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify(
                {
                    'success': False,
                    'error': 'Sign in required. Missing Authorization token.',
                }
            ), 401

        token = header[7:].strip()
        if not token:
            return jsonify({'success': False, 'error': 'Sign in required.'}), 401

        try:
            decoded = verify_id_token(token)
            g.firebase_uid = decoded['uid']
            g.firebase_email = decoded.get('email')
        except Exception as e:
            logger.warning('Firebase token verification failed: %s', e)
            return jsonify(
                {
                    'success': False,
                    'error': 'Session expired or invalid. Please sign in again.',
                }
            ), 401

        return view(*args, **kwargs)

    return wrapped
