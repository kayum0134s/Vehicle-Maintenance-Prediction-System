"""
Tests for VMPS configuration, URL normalization, and production checks.
"""
import os
import unittest
from unittest.mock import patch

from config import (
    normalize_database_url,
    get_database_uri,
    get_secret_key,
    get_debug_mode,
    get_engine_options,
    is_production,
    Config,
)


class TestConfig(unittest.TestCase):

    def test_normalize_database_url_schemes(self):
        """Test normalization across all supported PostgreSQL URL schemes."""
        cases = [
            (
                "postgres://user:pass@host:5432/db",
                "postgresql+psycopg://user:pass@host:5432/db"
            ),
            (
                "postgresql://user:pass@host:5432/db",
                "postgresql+psycopg://user:pass@host:5432/db"
            ),
            (
                "postgresql+psycopg2://user:pass@host:5432/db",
                "postgresql+psycopg://user:pass@host:5432/db"
            ),
            (
                "postgresql+psycopg://user:pass@host:5432/db",
                "postgresql+psycopg://user:pass@host:5432/db"
            ),
        ]
        for input_url, expected in cases:
            with self.subTest(input_url=input_url):
                self.assertEqual(normalize_database_url(input_url), expected)

    def test_normalize_preserves_encoded_passwords_and_params(self):
        """Ensure special characters in passwords and query parameters are preserved."""
        url = "postgresql://postgres.myproject:P%40ssw0rd%21%23@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&application_name=vmps"
        normalized = normalize_database_url(url)
        self.assertTrue(normalized.startswith("postgresql+psycopg://"))
        self.assertIn("P%40ssw0rd%21%23", normalized)
        self.assertIn("sslmode=require", normalized)
        self.assertIn("application_name=vmps", normalized)
        self.assertIn(":6543/postgres", normalized)

    def test_normalize_strips_quotes(self):
        """Quotes commonly pasted from .env files are stripped."""
        url = '"postgresql://user:pass@host:5432/db?sslmode=require"'
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg://user:pass@host:5432/db?sslmode=require"
        )

    def test_production_detection(self):
        """Verify is_production detects Vercel or production env flags."""
        with patch.dict(os.environ, {"VERCEL": "1"}, clear=True):
            self.assertTrue(is_production())
        with patch.dict(os.environ, {"VERCEL_ENV": "production"}, clear=True):
            self.assertTrue(is_production())
        with patch.dict(os.environ, {"FLASK_ENV": "production"}, clear=True):
            self.assertTrue(is_production())
        with patch.dict(os.environ, {"ENV": "production"}, clear=True):
            self.assertTrue(is_production())
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_production())

    def test_missing_database_url_in_production_raises_error(self):
        """Production must raise a clear configuration error when DATABASE_URL is missing."""
        with patch.dict(os.environ, {"VERCEL": "1", "DATABASE_URL": ""}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_database_uri()
            self.assertIn("DATABASE_URL", str(ctx.exception))
            self.assertIn("production", str(ctx.exception).lower())

    def test_sqlite_in_production_raises_error(self):
        """Production must reject SQLite to prevent read-only filesystem crash."""
        with patch.dict(os.environ, {"VERCEL": "1", "DATABASE_URL": "sqlite:///test.db"}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_database_uri()
            self.assertIn("SQLite is not supported in production", str(ctx.exception))

    def test_missing_secret_key_in_production_raises_error(self):
        """Production must require an explicit SECRET_KEY."""
        with patch.dict(os.environ, {"VERCEL": "1", "SECRET_KEY": ""}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_secret_key()
            self.assertIn("SECRET_KEY", str(ctx.exception))

    def test_debug_disabled_in_production(self):
        """DEBUG must be False in production even if DEBUG=True is passed."""
        with patch.dict(os.environ, {"VERCEL": "1", "DEBUG": "True"}, clear=True):
            self.assertFalse(get_debug_mode())

    def test_serverless_engine_options(self):
        """Verify engine options for PostgreSQL disable prepared statements for pooler."""
        pg_uri = "postgresql+psycopg://user:pass@pooler.supabase.com:6543/postgres"
        options = get_engine_options(pg_uri)
        self.assertTrue(options.get("pool_pre_ping"))
        self.assertEqual(options.get("connect_args", {}).get("prepare_threshold"), None)
        self.assertIn("pool_size", options)
        self.assertIn("max_overflow", options)


if __name__ == '__main__':
    unittest.main()
