"""
Vehicle Maintenance Prediction System (VMPS)
Configuration Module for Local Development & Supabase PostgreSQL (Vercel Serverless)
"""
import os
import urllib.parse
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()


def is_production() -> bool:
    """Detect if the application is running in production or Vercel serverless."""
    return bool(
        os.environ.get('VERCEL') == '1'
        or 'VERCEL_ENV' in os.environ
        or os.environ.get('FLASK_ENV') == 'production'
        or os.environ.get('ENV') == 'production'
    )


def normalize_database_url(url: str) -> str:
    """Normalize supported PostgreSQL URL schemes to postgresql+psycopg:// (Psycopg 3).

    Preserves credentials (including percent-encoded passwords), host, port, path,
    and query parameters without corruption.
    """
    if not url:
        return url
    url = url.strip()
    # Strip any enclosing quotation marks that might be in .env files
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1].strip()

    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme.lower()

    if scheme in ('postgres', 'postgresql', 'postgresql+psycopg2', 'postgresql+psycopg'):
        return parsed._replace(scheme='postgresql+psycopg').geturl()

    return url


def get_database_uri() -> str:
    """Retrieve and validate the database connection URI.

    In Production / Vercel:
      - DATABASE_URL is strictly required.
      - Never silently falls back to SQLite.
      - Disallows SQLite (read-only filesystem on Vercel).
      - Normalizes connection string to Psycopg 3 driver (postgresql+psycopg://).
    In Development:
      - Normalizes DATABASE_URL if provided.
      - Falls back to local SQLite with an explicit absolute path.
    """
    raw_url = os.environ.get('DATABASE_URL', '').strip()
    if (raw_url.startswith('"') and raw_url.endswith('"')) or (raw_url.startswith("'") and raw_url.endswith("'")):
        raw_url = raw_url[1:-1].strip()

    if is_production():
        if not raw_url:
            raise RuntimeError(
                "Missing required environment variable 'DATABASE_URL' in production. "
                "Please configure your Supabase PostgreSQL connection string in your Vercel project environment variables."
            )
        if raw_url.startswith('sqlite'):
            raise RuntimeError(
                "SQLite is not supported in production serverless environments (read-only filesystem). "
                "Please configure a valid PostgreSQL / Supabase connection string in DATABASE_URL."
            )
        return normalize_database_url(raw_url)

    # Development mode
    if raw_url:
        return normalize_database_url(raw_url)

    # Local SQLite fallback for development only, using absolute path
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    try:
        os.makedirs(instance_dir, exist_ok=True)
    except OSError:
        pass
    db_path = os.path.join(instance_dir, 'vehicle_maintenance.db')
    return f"sqlite:///{db_path.replace(os.sep, '/')}"


def get_secret_key() -> str:
    """Retrieve SECRET_KEY with strict validation in production."""
    secret = os.environ.get('SECRET_KEY', '').strip()
    if is_production():
        if not secret:
            raise RuntimeError(
                "Missing required environment variable 'SECRET_KEY' in production. "
                "Please configure a strong, random secret key in your Vercel project environment variables."
            )
        return secret
    return secret or 'vmps-2095-dev-secret-key-change-in-production'


def get_debug_mode() -> bool:
    """Disable debug mode in production; allow env override in development."""
    if is_production():
        return False
    return os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')


def get_engine_options(db_uri: str) -> dict:
    """Configure conservative SQLAlchemy connection pooling for serverless execution.

    Optimized for Supabase Transaction Pooler (Supavisor/PgBouncer port 6543)
    and serverless container lifecycles:
      - pool_pre_ping: Verifies connection liveness before checkout.
      - prepare_threshold: None: Disables automatic prepared statements in Psycopg 3,
        which is required for transaction-mode connection poolers.
      - pool_size / max_overflow: Kept small to prevent connection pool exhaustion.
      - pool_recycle: Recycles connections periodically to avoid stale connections.
    """
    options = {
        'pool_pre_ping': True,
    }

    if db_uri and db_uri.startswith('postgresql'):
        pool_size = int(os.environ.get('DB_POOL_SIZE', '5'))
        max_overflow = int(os.environ.get('DB_MAX_OVERFLOW', '2'))
        pool_recycle = int(os.environ.get('DB_POOL_RECYCLE', '300'))
        pool_timeout = int(os.environ.get('DB_POOL_TIMEOUT', '30'))

        options.update({
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_recycle': pool_recycle,
            'pool_timeout': pool_timeout,
            'connect_args': {
                # Essential for Supabase Transaction Pooler (port 6543)
                'prepare_threshold': None,
            }
        })
    elif db_uri and db_uri.startswith('sqlite'):
        options.update({
            'connect_args': {
                'check_same_thread': False
            }
        })

    return options


class ConfigMeta(type):
    """Metaclass allowing class-level dynamic property evaluation."""
    @property
    def SQLALCHEMY_DATABASE_URI(cls):
        return get_database_uri()

    @property
    def SECRET_KEY(cls):
        return get_secret_key()

    @property
    def DEBUG(cls):
        return get_debug_mode()

    @property
    def SQLALCHEMY_ENGINE_OPTIONS(cls):
        return get_engine_options(cls.SQLALCHEMY_DATABASE_URI)


class Config(metaclass=ConfigMeta):
    """Base application configuration class."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def init_app(cls, app):
        """Apply and validate configuration settings on the Flask app."""
        db_uri = get_database_uri()
        secret_key = get_secret_key()
        debug_mode = get_debug_mode()
        engine_options = get_engine_options(db_uri)

        app.config['SECRET_KEY'] = secret_key
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEBUG'] = debug_mode
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
