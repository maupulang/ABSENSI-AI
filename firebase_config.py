import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

FIREBASE_DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL", 
    "https://absensi-ai-a8281-default-rtdb.firebaseio.com"
).rstrip('/')
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "absensi-ai-a8281")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "absensi-ai-a8281.firebasestorage.app")
FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "serviceAccountKey.json")
FIREBASE_DB_SECRET = os.getenv("FIREBASE_DB_SECRET", "")

_firebase_admin_initialized = False
_db_mode = "rest" # 'admin' or 'rest'

# Try initializing Firebase Admin SDK if service account exists
try:
    import firebase_admin
    from firebase_admin import credentials, db as admin_db, auth as admin_auth

    if os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY):
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DATABASE_URL,
            'storageBucket': FIREBASE_STORAGE_BUCKET
        })
        _firebase_admin_initialized = True
        _db_mode = "admin"
        logger.info("Firebase Admin SDK successfully initialized using service account.")
    else:
        logger.warning(
            f"Service account file '{FIREBASE_SERVICE_ACCOUNT_KEY}' not found. "
            "Falling back to Firebase Realtime Database REST API client."
        )
except Exception as e:
    logger.warning(f"Could not initialize Firebase Admin SDK: {e}. Using REST API client.")


class FirebaseRestDB:
    """Fallback REST API client for Firebase Realtime Database."""
    def __init__(self, base_url, db_secret=""):
        self.base_url = base_url.rstrip('/')
        self.db_secret = db_secret

    def _build_url(self, path):
        clean_path = path.strip('/')
        url = f"{self.base_url}/{clean_path}.json"
        if self.db_secret:
            url += f"?auth={self.db_secret}"
        return url

    def get(self, path):
        url = self._build_url(path)
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            logger.error(f"Firebase REST GET {url} failed: {resp.status_code} - {resp.text}")
            return None
        except Exception as err:
            logger.error(f"Firebase REST GET exception: {err}")
            return None

    def set(self, path, data):
        url = self._build_url(path)
        try:
            resp = requests.put(url, json=data, timeout=10)
            return resp.status_code in [200, 201]
        except Exception as err:
            logger.error(f"Firebase REST PUT exception: {err}")
            return False

    def update(self, path, data):
        url = self._build_url(path)
        try:
            resp = requests.patch(url, json=data, timeout=10)
            return resp.status_code == 200
        except Exception as err:
            logger.error(f"Firebase REST PATCH exception: {err}")
            return False

    def push(self, path, data):
        url = self._build_url(path)
        try:
            resp = requests.post(url, json=data, timeout=10)
            if resp.status_code in [200, 201]:
                return resp.json().get('name')
            return None
        except Exception as err:
            logger.error(f"Firebase REST POST exception: {err}")
            return None

    def delete(self, path):
        url = self._build_url(path)
        try:
            resp = requests.delete(url, timeout=10)
            return resp.status_code == 200
        except Exception as err:
            logger.error(f"Firebase REST DELETE exception: {err}")
            return False


class FirebaseAdminDBAdapter:
    """Adapter for Firebase Admin SDK Realtime Database."""
    def get(self, path):
        ref = admin_db.reference(path)
        return ref.get()

    def set(self, path, data):
        ref = admin_db.reference(path)
        ref.set(data)
        return True

    def update(self, path, data):
        ref = admin_db.reference(path)
        ref.update(data)
        return True

    def push(self, path, data):
        ref = admin_db.reference(path)
        new_ref = ref.push(data)
        return new_ref.key

    def delete(self, path):
        ref = admin_db.reference(path)
        ref.delete()
        return True


def get_db():
    """Returns active database client (Admin SDK or REST client)."""
    if _firebase_admin_initialized:
        return FirebaseAdminDBAdapter()
    return FirebaseRestDB(FIREBASE_DATABASE_URL, FIREBASE_DB_SECRET)


def verify_id_token(id_token):
    """Verify Firebase ID token if Admin SDK is available."""
    if _firebase_admin_initialized:
        try:
            decoded = admin_auth.verify_id_token(id_token)
            return decoded
        except Exception as err:
            logger.error(f"Token verification error: {err}")
            return None
    return None


def get_web_firebase_config():
    """Returns configuration object for frontend Firebase SDK."""
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyBLnZnaR_nnW8ds4Zhe554lGAXUl3VVHXE"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "absensi-ai-a8281.firebaseapp.com"),
        "databaseURL": FIREBASE_DATABASE_URL,
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "778160501517"),
        "appId": os.getenv("FIREBASE_APP_ID", "1:778160501517:web:0917fbbb87420221d47644")
    }
