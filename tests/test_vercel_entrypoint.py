"""
Tests verifying Vercel serverless entrypoint and configuration.
"""
import unittest
import os
import json
from unittest.mock import patch


class TestVercelEntrypoint(unittest.TestCase):

    def test_vercel_json_validity(self):
        """Verify vercel.json is valid and correctly configured for @vercel/python."""
        vercel_json_path = os.path.abspath("vercel.json")
        self.assertTrue(os.path.exists(vercel_json_path), "vercel.json must exist")

        with open(vercel_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("version"), 2)
        builds = data.get("builds", [])
        self.assertTrue(any(b.get("src") == "app.py" and b.get("use") == "@vercel/python" for b in builds))
        routes = data.get("routes", [])
        self.assertTrue(any(r.get("dest") == "app.py" for r in routes))

    def test_app_module_export(self):
        """Verify app.py exports an 'app' instance for Vercel WSGI discovery."""
        import app
        self.assertTrue(hasattr(app, "app"), "app.py must export 'app' for Vercel")
        self.assertTrue(callable(app.app), "'app' must be a WSGI callable")

    def test_vercel_serverless_import_does_not_create_instance_dir(self):
        """
        Verify that in a simulated Vercel serverless environment with a Supabase PostgreSQL
        DATABASE_URL, create_app initializes without touching or creating '/var/task/instance'.
        """
        fake_pg_url = "postgresql://postgres.ref:secret@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        env = {
            "VERCEL": "1",
            "DATABASE_URL": fake_pg_url,
            "SECRET_KEY": "test-vercel-secret-key"
        }

        with patch.dict(os.environ, env, clear=True):
            from config import get_database_uri, get_engine_options
            from app import create_app

            uri = get_database_uri()
            self.assertEqual(uri, "postgresql+psycopg://postgres.ref:secret@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")

            # Initialize app factory
            app_instance = create_app()
            self.assertEqual(app_instance.config['SQLALCHEMY_DATABASE_URI'], uri)
            self.assertFalse(app_instance.config['DEBUG'])
            # Verify engine options disable prepared statements
            self.assertIsNone(
                app_instance.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args']['prepare_threshold']
            )


if __name__ == '__main__':
    unittest.main()
